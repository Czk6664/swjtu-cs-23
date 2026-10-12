package com.swjtu.forum;

import org.junit.jupiter.api.*;
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.Select;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;

import static org.junit.jupiter.api.Assertions.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class ForumBlackBoxTest {
    private static final String BASE_URL = System.getProperty("forum.baseUrl", "http://localhost:4173");
    private static WebDriver driver;
    private static WebDriverWait wait;
    private static final String ADMIN = "admin";
    private static final String ADMIN_PASSWORD = "admin123456";

    @BeforeAll
    static void setUp() {
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--remote-allow-origins=*", "--window-size=1440,1000");
        options.setBinary("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe");
        driver = new ChromeDriver(options);
        wait = new WebDriverWait(driver, Duration.ofSeconds(15));
    }

    @AfterAll
    static void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }

    @Test
    @Order(1)
    void loginBrowseFilterAndSearch() {
        loginAsAdmin();
        driver.get(BASE_URL + "/home_recommended_desktop/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("main article")));
        assertTrue(driver.findElements(By.cssSelector("main article")).size() >= 1);

        Select section = new Select(driver.findElement(By.cssSelector("main select")));
        section.selectByIndex(1);
        click(By.cssSelector("[data-search-form] button[type='submit']"));
        wait.until(ExpectedConditions.urlContains("sectionId="));

        driver.get(BASE_URL + "/home_recommended_desktop/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-search-form] input[name='keyword']")));
        driver.findElement(By.cssSelector("[data-search-form] input[name='keyword']")).sendKeys("签到");
        click(By.cssSelector("[data-search-form] button[type='submit']"));
        wait.until(ExpectedConditions.or(
                ExpectedConditions.urlContains("keyword="),
                ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "签到")
        ));
    }

    @Test
    @Order(2)
    void notificationPanelMustBecomeVisible() {
        loginAsAdmin();
        driver.get(BASE_URL + "/home_recommended_desktop/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-notif-toggle]")));
        click(By.cssSelector("[data-notif-toggle]"));
        WebElement panel = wait.until(ExpectedConditions.presenceOfElementLocated(By.cssSelector("[data-notif-panel]")));
        Boolean hidden = (Boolean) ((JavascriptExecutor) driver).executeScript("return arguments[0].hidden;", panel);
        String display = (String) ((JavascriptExecutor) driver).executeScript("return getComputedStyle(arguments[0]).display;", panel);
        assertFalse(hidden, "notification panel should not be hidden after clicking bell");
        assertNotEquals("none", display, "notification panel display should not be none");
        assertEquals("true", driver.findElement(By.cssSelector("[data-notif-toggle]")).getAttribute("aria-expanded"));
    }

    @Test
    @Order(3)
    void rewardsAndRedemptionsMustLoadWithoutServerError() {
        loginAsAdmin();
        driver.get(BASE_URL + "/rewards_mall/code.html");
        wait.until(ExpectedConditions.not(ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "页面加载失败")));
        assertFalse(driver.getPageSource().contains("Internal Server Error"));
        assertTrue(driver.getPageSource().contains("积分") || driver.findElements(By.cssSelector("[data-redeem]")).size() > 0);
    }

    @Test
    @Order(4)
    void createCommentLikeFavoriteAndFollow() {
        loginAsAdmin();
        driver.get(BASE_URL + "/post_details/code.html?id=1");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("body")));

        if (driver.findElements(By.cssSelector("[data-comment-form] textarea[name='content']")).size() > 0) {
            driver.findElement(By.cssSelector("[data-comment-form] textarea[name='content']")).sendKeys("Selenium black-box comment");
            click(By.cssSelector("[data-comment-form] button[type='submit']"));
            wait.until(ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("body"), "Selenium black-box comment"));
        }
        if (driver.findElements(By.cssSelector("[data-like-post]")).size() > 0) {
            click(By.cssSelector("[data-like-post]"));
        }
        if (driver.findElements(By.cssSelector("[data-favorite]")).size() > 0) {
            click(By.cssSelector("[data-favorite]"));
        }
        if (driver.findElements(By.cssSelector("[data-follow]")).size() > 0) {
            click(By.cssSelector("[data-follow]"));
            wait.until(ExpectedConditions.presenceOfElementLocated(By.cssSelector("[data-follow]")));
        }
    }

    private static void loginAsAdmin() {
        driver.get(BASE_URL + "/home_recommended_desktop/code.html");
        try {
            new WebDriverWait(driver, Duration.ofSeconds(4))
                    .until(ExpectedConditions.presenceOfElementLocated(By.cssSelector("[data-notif-toggle]")));
            return;
        } catch (TimeoutException ignored) {
            ((JavascriptExecutor) driver).executeScript("window.localStorage.clear(); window.sessionStorage.clear();");
        }

        driver.get(BASE_URL + "/login_register/code.html");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("[data-auth-form='login']")));
        WebElement username = driver.findElement(By.cssSelector("[data-auth-form='login'] input[name='username']"));
        username.clear();
        username.sendKeys(ADMIN);
        WebElement password = driver.findElement(By.cssSelector("[data-auth-form='login'] input[name='password']"));
        password.clear();
        password.sendKeys(ADMIN_PASSWORD);
        click(By.cssSelector("[data-auth-form='login'] [data-auth-submit]"));
        wait.until(ExpectedConditions.or(
                ExpectedConditions.urlContains("home_recommended"),
                ExpectedConditions.presenceOfElementLocated(By.cssSelector("[data-notif-toggle]"))
        ));
    }

    private static void click(By locator) {
        StaleElementReferenceException last = null;
        for (int i = 0; i < 3; i++) {
            try {
                WebElement element = wait.until(ExpectedConditions.refreshed(
                        ExpectedConditions.presenceOfElementLocated(locator)));
                ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({block:'center'});", element);
                ((JavascriptExecutor) driver).executeScript("arguments[0].click();", element);
                return;
            } catch (StaleElementReferenceException error) {
                last = error;
                try {
                    Thread.sleep(300);
                } catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                }
            }
        }
        throw last;
    }
}
