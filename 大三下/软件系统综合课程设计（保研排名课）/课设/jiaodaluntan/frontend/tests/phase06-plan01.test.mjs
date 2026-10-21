import { strict as assert } from 'node:assert'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { resolve } from 'node:path'

const root = process.cwd().endsWith('frontend') ? process.cwd() : resolve(process.cwd(), 'frontend')

const read = (relativePath) => readFileSync(resolve(root, relativePath), 'utf8')
const readRuntimeSources = (relativePath) => {
  const absolutePath = resolve(root, relativePath)
  return readdirSync(absolutePath)
    .flatMap((entry) => {
      const child = resolve(absolutePath, entry)
      if (statSync(child).isDirectory()) {
        return readdirSync(child).map((nested) => readFileSync(resolve(child, nested), 'utf8'))
      }
      return entry.endsWith('.js') ? [readFileSync(child, 'utf8')] : []
    })
    .join('\n')
}

const appJs = read('assets/app.js')
const packageJson = JSON.parse(read('package.json'))
// The shared runtime now lives in ES modules under assets/modules/; app.js is only
// the entry dispatcher. Assertions on shared behavior read app.js + every module.
const jsSources = `${appJs}\n${readRuntimeSources('assets/modules')}`
const homeMobileHtml = read('home_recommended/code.html')
const homeDesktopHtml = read('home_recommended_desktop/code.html')
const postDetailHtml = read('post_details/code.html')
const profileHtml = read('profile_overview/code.html')
const growthHtml = read('growth_center/code.html')
const rewardsHtml = read('rewards_mall/code.html')
const adminHtml = read('admin_overview/code.html')
const userMobileHtml = read('user_management/code.html')
const userDesktopHtml = read('user_management_desktop/code.html')
const rewardsRuntime = read('assets/modules/pages/rewards.js')

const requiredShellMarkers = [
  [homeMobileHtml, 'data-slot="home-mobile-feed"'],
  [homeDesktopHtml, 'data-slot="home-desktop-feed"'],
  [postDetailHtml, 'data-slot="post-detail-content"'],
  [profileHtml, 'data-slot="profile-content"'],
  [growthHtml, 'data-slot="growth-content"'],
  [rewardsHtml, 'data-slot="rewards-content"'],
  [adminHtml, 'data-slot="admin-overview-content"'],
  [userMobileHtml, 'data-slot="user-management-mobile-content"'],
  [userDesktopHtml, 'data-slot="user-management-desktop-content"']
]

requiredShellMarkers.forEach(([content, marker]) => {
  assert.ok(content.includes(marker), `missing shell marker: ${marker}`)
})

const forbiddenPrototypeStrings = [
  'Dr. Chen Wei',
  'Golden hour at the Main Library',
  'This post is pending review by the academic board.',
  'Available Points Balance',
  'Current Level',
  'Academic Pioneer',
  'Wei Chen',
  'Dr. James Doe',
  'Dr. Wei Zhang',
  'Fetching more intellectual content...'
]

forbiddenPrototypeStrings.forEach((snippet) => {
  const files = [homeMobileHtml, homeDesktopHtml, postDetailHtml, profileHtml, growthHtml, rewardsHtml, adminHtml, userMobileHtml, userDesktopHtml]
  files.forEach((content) => {
    assert.ok(!content.includes(snippet), `prototype content leaked: ${snippet}`)
  })
})

assert.ok(jsSources.includes('post-detail-content'), 'post detail shell slot not used in runtime modules')

assert.ok(jsSources.includes('history.pushState') || jsSources.includes('history.replaceState'), 'home page should sync state with history API')
assert.ok(appJs.includes('popstate'), 'home page should restore state from URL changes')
assert.ok(jsSources.includes('renderHome'), 'home should render through a shared renderHome helper')
assert.ok(appJs.includes('home-desktop') && appJs.includes('home-mobile'), 'entry should dispatch both desktop and mobile home pages')
assert.ok(jsSources.includes('escapeHtml'), 'runtime should expose a shared HTML escaping helper')
assert.ok(jsSources.includes('apiRequest'), 'runtime should use a shared API client')
assert.ok(jsSources.includes('AbortController'), 'shared API client should time out stalled requests')
assert.ok(jsSources.includes('REQUEST_TIMEOUT_MS'), 'shared API client should centralize request timeout')
assert.ok(jsSources.includes('fetchSections'), 'section loading should be cached within a page lifecycle')
assert.ok(jsSources.includes('invalidateSectionsCache'), 'section mutations should invalidate cached section data')
assert.ok(jsSources.includes('data-search-form'), 'home page should expose live search/filter form')
assert.ok(jsSources.includes('/posts/search?keyword='), 'home search should call live backend search endpoint')
assert.ok(jsSources.includes('/withdraw'), 'owned posts should support withdraw flow')
assert.ok(jsSources.includes('data-report-form'), 'post detail should expose report form')
assert.ok(jsSources.includes('data-profile-form'), 'profile should expose editable profile form')
assert.ok(jsSources.includes('data-section-form'), 'admin user page should expose section management form')
assert.ok(jsSources.includes('帖子已提交审核'), 'post creation should distinguish pending review from published success')
assert.ok(jsSources.includes('location.href = canEnterDestination ? next : ROUTES.home'), 'registration and login should continue to safe normal-user destinations')
assert.ok(jsSources.includes('注册或登录成功后，系统会自动回到发帖页。'), 'auth page should explain the create-post login flow')
assert.ok(jsSources.includes('后台功能仅管理员可访问，普通用户已返回论坛首页。'), 'normal users should be returned home instead of being trapped on an admin permission page')
assert.ok(jsSources.includes('普通用户可以继续进入论坛首页浏览、发帖和评论。'), '403 copy should clarify that normal users can continue using the forum')
assert.ok(appJs.includes('普通用户可以继续在论坛首页浏览、发帖、评论、收藏和签到。'), 'global 403 copy should explain the normal-user workflow')
assert.ok(appJs.includes('error.status === 403'), 'global bootstrap should handle 403 without rendering every page as failed')
assert.ok(appJs.includes('clearSession()'), '403 during page boot should clear stale sessions instead of looping')
assert.ok(!appJs.includes('location.replace(ROUTES.home)'), '403 during page boot must not create a refresh loop')
assert.ok(jsSources.includes('installMotionSystem'), 'runtime should install the shared product motion layer')
assert.ok(packageJson.dependencies?.animejs, 'anime.js must be declared as a package dependency for Vite bundling')
assert.ok(jsSources.includes('import("animejs")'), 'motion layer should import anime.js through Vite, not an external path')
assert.ok(!jsSources.includes('../../vendor/animejs/index.js'), 'runtime should not depend on a local vendor anime.js path')
assert.ok(!jsSources.includes('使用演示账号'), 'auth page must not expose demo-account shortcuts')
assert.ok(!jsSources.includes('admin / admin123456'), 'runtime must not reveal default admin credentials')
assert.ok(
  !rewardsRuntime.includes('adminMode || state.user?.role === "ADMIN"'),
  'topbar points mall must stay as the normal rewards mall even for admins'
)
assert.ok(
  rewardsRuntime.includes('document.body?.dataset.page === "admin-rewards"'),
  'admin reward management should only use the dedicated admin rewards page'
)
