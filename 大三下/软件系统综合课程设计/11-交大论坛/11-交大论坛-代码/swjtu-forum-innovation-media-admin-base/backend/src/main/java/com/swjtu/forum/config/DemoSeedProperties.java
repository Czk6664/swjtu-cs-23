package com.swjtu.forum.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Component;

import java.util.Arrays;

@Data
@Component
@ConfigurationProperties(prefix = "demo.seed")
public class DemoSeedProperties {

    private boolean enabled = false;
    private boolean runOnDemoProfile = true;

    public boolean shouldRun(Environment environment) {
        if (enabled) {
            return true;
        }
        return runOnDemoProfile && Arrays.stream(environment.getActiveProfiles()).anyMatch("demo"::equalsIgnoreCase);
    }
}
