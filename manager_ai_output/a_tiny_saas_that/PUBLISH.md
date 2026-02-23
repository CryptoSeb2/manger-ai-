# Publish A tiny SaaS that... online

## Option 1: Vercel (recommended)
1. Push this folder to a GitHub repo.
2. Go to [vercel.com](https://vercel.com) → Import project → select the repo.
3. Root directory: `a_tiny_saas_that` (or the folder containing `index.html`). Deploy.

## Option 2: Netlify
1. Drag the folder containing `index.html` to [app.netlify.com/drop](https://app.netlify.com/drop), or connect a Git repo.

## Option 3: GitHub Pages
1. Create a repo, push this folder. In Settings → Pages, set source to main branch and root (or /docs if you put files in docs/).

## Option 4: Use Cursor to build a full app
Use the Cursor prompt in `manager_ai_output/cursor_prompts/a_tiny_saas_that/build_in_cursor.md` to build a full app, then deploy that project to Vercel/Netlify.
