import com.sun.net.httpserver.Headers;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.Executors;

public class FrontendServer {
    private static final Map<String, String> MIME_TYPES = Map.ofEntries(
            Map.entry(".html", "text/html; charset=UTF-8"),
            Map.entry(".js", "application/javascript; charset=UTF-8"),
            Map.entry(".css", "text/css; charset=UTF-8"),
            Map.entry(".svg", "image/svg+xml"),
            Map.entry(".png", "image/png"),
            Map.entry(".jpg", "image/jpeg"),
            Map.entry(".jpeg", "image/jpeg"),
            Map.entry(".ico", "image/x-icon"),
            Map.entry(".json", "application/json; charset=UTF-8")
    );

    private final Path distDir;
    private final String backendBaseUrl;
    private final HttpClient client;

    private FrontendServer(Path distDir, int backendPort) {
        this.distDir = distDir.toAbsolutePath().normalize();
        this.backendBaseUrl = "http://127.0.0.1:" + backendPort;
        this.client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .followRedirects(HttpClient.Redirect.NEVER)
                .build();
    }

    public static void main(String[] args) throws Exception {
        Path dist = Path.of(args.length > 0 ? args[0] : "frontend/dist");
        int port = Integer.parseInt(args.length > 1 ? args[1] : "4173");
        int backendPort = Integer.parseInt(args.length > 2 ? args[2] : "8080");

        FrontendServer app = new FrontendServer(dist, backendPort);
        HttpServer server = HttpServer.create(new java.net.InetSocketAddress("127.0.0.1", port), 0);
        server.createContext("/", app::handle);
        server.setExecutor(Executors.newFixedThreadPool(8));
        server.start();
        System.out.println("Frontend server started: http://localhost:" + port);
        System.out.println("Proxy /api -> " + app.backendBaseUrl + "/api");
        System.out.println("Proxy /uploads -> " + app.backendBaseUrl + "/uploads");
    }

    private void handle(HttpExchange exchange) throws IOException {
        try {
            String path = exchange.getRequestURI().getPath();
            if (path.startsWith("/api/") || path.equals("/api")
                    || path.startsWith("/uploads/") || path.equals("/uploads")) {
                proxyBackend(exchange);
                return;
            }
            serveStatic(exchange);
        } catch (Exception ex) {
            byte[] body = ("Internal server error: " + ex.getMessage()).getBytes(java.nio.charset.StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(500, body.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(body);
            }
        }
    }

    private void proxyBackend(HttpExchange exchange) throws IOException, InterruptedException {
        URI source = exchange.getRequestURI();
        URI target = URI.create(backendBaseUrl + source.getRawPath()
                + (source.getRawQuery() == null ? "" : "?" + source.getRawQuery()));

        HttpRequest.BodyPublisher bodyPublisher;
        try (InputStream body = exchange.getRequestBody()) {
            byte[] requestBody = body.readAllBytes();
            bodyPublisher = requestBody.length == 0
                    ? HttpRequest.BodyPublishers.noBody()
                    : HttpRequest.BodyPublishers.ofByteArray(requestBody);
        }

        HttpRequest.Builder builder = HttpRequest.newBuilder(target)
                .timeout(Duration.ofSeconds(30))
                .method(exchange.getRequestMethod(), bodyPublisher);

        copyRequestHeaders(exchange.getRequestHeaders(), builder);
        HttpResponse<byte[]> response = client.send(builder.build(), HttpResponse.BodyHandlers.ofByteArray());

        Headers headers = exchange.getResponseHeaders();
        response.headers().map().forEach((name, values) -> {
            if (!isHopByHopHeader(name)) {
                headers.put(name, values);
            }
        });
        exchange.sendResponseHeaders(response.statusCode(), response.body().length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(response.body());
        }
    }

    private void serveStatic(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())
                && !"HEAD".equalsIgnoreCase(exchange.getRequestMethod())) {
            exchange.sendResponseHeaders(405, -1);
            return;
        }

        String rawPath = exchange.getRequestURI().getPath();
        String relative = rawPath.equals("/") ? "index.html" : rawPath.substring(1);
        Path file = distDir.resolve(relative).normalize();
        if (!file.startsWith(distDir) || Files.isDirectory(file) || !Files.exists(file)) {
            file = distDir.resolve("index.html").normalize();
        }

        byte[] body = Files.readAllBytes(file);
        exchange.getResponseHeaders().set("Content-Type", contentType(file));
        exchange.sendResponseHeaders(200, "HEAD".equalsIgnoreCase(exchange.getRequestMethod()) ? -1 : body.length);
        if (!"HEAD".equalsIgnoreCase(exchange.getRequestMethod())) {
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(body);
            }
        }
    }

    private void copyRequestHeaders(Headers source, HttpRequest.Builder target) {
        for (Map.Entry<String, List<String>> entry : source.entrySet()) {
            String name = entry.getKey();
            if (isHopByHopHeader(name) || "host".equalsIgnoreCase(name)) {
                continue;
            }
            for (String value : entry.getValue()) {
                target.header(name, value);
            }
        }
    }

    private static boolean isHopByHopHeader(String name) {
        String lower = name.toLowerCase(Locale.ROOT);
        return lower.equals("connection")
                || lower.equals("content-length")
                || lower.equals("expect")
                || lower.equals("host")
                || lower.equals("keep-alive")
                || lower.equals("proxy-authenticate")
                || lower.equals("proxy-authorization")
                || lower.equals("te")
                || lower.equals("trailer")
                || lower.equals("transfer-encoding")
                || lower.equals("upgrade");
    }

    private static String contentType(Path file) {
        String name = file.getFileName().toString().toLowerCase(Locale.ROOT);
        for (Map.Entry<String, String> entry : MIME_TYPES.entrySet()) {
            if (name.endsWith(entry.getKey())) {
                return entry.getValue();
            }
        }
        return "application/octet-stream";
    }
}
