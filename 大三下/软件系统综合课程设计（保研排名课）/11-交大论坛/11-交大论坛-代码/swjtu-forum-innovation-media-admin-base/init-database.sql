-- Phase 1 bootstrap entry.
-- MySQL bootstrap entry.
-- It only creates the database. Tables and seed data are managed by Spring Boot JPA and Java seeders.

SET NAMES utf8mb4;
CREATE DATABASE IF NOT EXISTS swjtu_forum CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE swjtu_forum;

SELECT 'SWJTU forum database is ready. Start backend with spring.profiles.active=mysql.' AS Message;
