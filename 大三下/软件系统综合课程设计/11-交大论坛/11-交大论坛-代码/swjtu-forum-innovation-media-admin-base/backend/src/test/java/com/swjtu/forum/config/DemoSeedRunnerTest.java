package com.swjtu.forum.config;

import com.swjtu.forum.service.DemoSeeder;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.boot.DefaultApplicationArguments;
import org.springframework.core.env.Environment;

import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class DemoSeedRunnerTest {

    @Mock
    private DemoSeeder demoSeeder;
    @Mock
    private Environment environment;

    @Test
    void runSkipsSeedByDefault() throws Exception {
        DemoSeedProperties properties = new DemoSeedProperties();
        DemoSeedRunner demoSeedRunner = new DemoSeedRunner(properties, demoSeeder, environment);
        when(environment.getActiveProfiles()).thenReturn(new String[]{});

        demoSeedRunner.run(new DefaultApplicationArguments(new String[]{}));

        verify(demoSeeder, never()).seed();
    }

    @Test
    void runExecutesSeedWhenGuardAllowsIt() throws Exception {
        DemoSeedProperties properties = new DemoSeedProperties();
        DemoSeedRunner demoSeedRunner = new DemoSeedRunner(properties, demoSeeder, environment);
        when(environment.getActiveProfiles()).thenReturn(new String[]{"demo"});

        demoSeedRunner.run(new DefaultApplicationArguments(new String[]{}));

        verify(demoSeeder).seed();
    }
}
