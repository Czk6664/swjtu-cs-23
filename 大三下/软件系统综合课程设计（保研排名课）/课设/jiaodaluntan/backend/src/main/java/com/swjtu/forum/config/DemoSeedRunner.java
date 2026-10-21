package com.swjtu.forum.config;

import com.swjtu.forum.service.DemoSeeder;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Component;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Component
public class DemoSeedRunner implements ApplicationRunner {

    private static final Logger log = LoggerFactory.getLogger(DemoSeedRunner.class);

    private final DemoSeedProperties properties;
    private final DemoSeeder demoSeeder;
    private final Environment environment;

    public DemoSeedRunner(DemoSeedProperties properties, DemoSeeder demoSeeder, Environment environment) {
        this.properties = properties;
        this.demoSeeder = demoSeeder;
        this.environment = environment;
    }

    @Override
    public void run(ApplicationArguments args) {
        if (!properties.shouldRun(environment)) {
            log.debug("Skip demo seed because profile/property guard is disabled");
            return;
        }
        demoSeeder.seed();
    }
}
