package com.swjtu.forum;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

@SpringBootApplication
@EnableJpaAuditing
public class ForumApplication {
    public static void main(String[] args) {
        SpringApplication.run(ForumApplication.class, args);
    }
}
