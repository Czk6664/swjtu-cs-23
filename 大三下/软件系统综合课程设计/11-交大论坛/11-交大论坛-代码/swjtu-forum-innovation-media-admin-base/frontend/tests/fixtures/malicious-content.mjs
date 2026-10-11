export const maliciousText = '<img src=x onerror="globalThis.__xssExecuted=true"><script>globalThis.__xssExecuted=true</script>';

export const maliciousPost = {
  id: 101,
  title: maliciousText,
  content: maliciousText,
  section: { name: maliciousText },
  author: { username: maliciousText },
  tags: [{ name: maliciousText }],
  recommendationReasons: [maliciousText],
  commentCount: 1,
  collectCount: 1,
  viewCount: 1
};

export const maliciousCategories = {
  postTitle: maliciousText,
  postContent: maliciousText,
  commentContent: maliciousText,
  username: maliciousText,
  reportReason: maliciousText,
  rewardDescription: maliciousText,
  recommendationPreview: maliciousText
};
