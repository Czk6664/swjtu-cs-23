import { defineConfig } from 'vite'
import { resolve } from 'path'

const entry = (...segments) => resolve(__dirname, ...segments)

// 后端端口可通过环境变量 BACKEND_PORT 覆盖（默认 8080），便于一键启动脚本换端口
const backendPort = process.env.BACKEND_PORT || 8080

export default defineConfig({
  appType: 'mpa',
  root: __dirname,
  publicDir: false,
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: `http://localhost:${backendPort}`,
        changeOrigin: true
      },
      '/uploads': {
        target: `http://localhost:${backendPort}`,
        changeOrigin: true
      }
    }
  },
  preview: {
    port: 4173,
    proxy: {
      '/api': {
        target: `http://localhost:${backendPort}`,
        changeOrigin: true
      },
      '/uploads': {
        target: `http://localhost:${backendPort}`,
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: resolve(__dirname, 'dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        index: entry('index.html'),
        homeMobile: entry('home_recommended', 'code.html'),
        homeDesktop: entry('home_recommended_desktop', 'code.html'),
        loginRegister: entry('login_register', 'code.html'),
        createPost: entry('create_post', 'code.html'),
        postDetail: entry('post_details', 'code.html'),
        profileOverview: entry('profile_overview', 'code.html'),
        circleCenter: entry('circle_center', 'code.html'),
        assetPreview: entry('asset_preview', 'code.html'),
        growthCenter: entry('growth_center', 'code.html'),
        rewardsMall: entry('rewards_mall', 'code.html'),
        adminOverview: entry('admin_overview', 'code.html'),
        adminRewards: entry('admin_rewards', 'code.html'),
        contentGovernance: entry('content_governance', 'code.html'),
        userManagement: entry('user_management', 'code.html'),
        userManagementDesktop: entry('user_management_desktop', 'code.html'),
        recommendationStrategy: entry('recommendation_strategy', 'code.html'),
        recommendationStrategyDesktop: entry('recommendation_strategy_desktop', 'code.html')
      }
    }
  }
})
