const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 720 });
  const html = `
    <!DOCTYPE html>
    <html lang="ja">
    <head>
      <meta charset="UTF-8">
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@700&family=Noto+Sans+JP:wght@700&display=swap');
        body {
          margin: 0;
          padding: 0;
          width: 1280px;
          height: 720px;
          background-color: #111827;
          display: flex;
          flex-direction: column;
          justify-content: center;
          box-sizing: border-box;
          padding-left: 120px;
          font-family: 'Inter', 'Noto Sans JP', sans-serif;
        }
        .line1 {
          color: #ffffff;
          font-size: 96px;
          font-weight: 700;
          letter-spacing: -0.02em;
          margin-bottom: 24px;
        }
        .line2 {
          color: #ffffff;
          font-size: 72px;
          font-weight: 700;
          margin-bottom: 32px;
          letter-spacing: 0.02em;
        }
        .line3 {
          color: #8ecae6;
          font-size: 48px;
          font-weight: 700;
          letter-spacing: 0.04em;
        }
      </style>
    </head>
    <body>
      <div class="line1">Next.js / Stripe</div>
      <div class="line2">不具合診断・修正します</div>
      <div class="line3">Webhook・API連携対応</div>
    </body>
    </html>
  `;
  await page.setContent(html);
  
  // Wait for fonts to load properly
  await page.evaluate(async () => {
    await document.fonts.ready;
  });

  await page.screenshot({ path: '/home/hr-hm/Project/work/banner.png' });
  await browser.close();
})();
