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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+JP:wght@400;600;700&display=swap');
        body {
          margin: 0;
          padding: 0;
          width: 1280px;
          height: 720px;
          background: linear-gradient(to right, #0d1b2a, #162d3e);
          font-family: 'Inter', 'Noto Sans JP', sans-serif;
          overflow: hidden;
          position: relative;
        }

        /* Abstract geometric hexagon pattern */
        .hex-pattern {
          position: absolute;
          bottom: 0;
          right: 0;
          width: 800px;
          height: 800px;
          opacity: 0.08;
          z-index: 1;
          pointer-events: none;
          -webkit-mask-image: radial-gradient(circle at 80% 80%, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 60%);
          mask-image: radial-gradient(circle at 80% 80%, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 60%);
        }

        /* Subtle geometric element closer to the center */
        .center-hex {
          position: absolute;
          top: 15%;
          left: 10%;
          width: 450px;
          height: 450px;
          opacity: 0.04;
          z-index: 1;
          pointer-events: none;
        }

        .content-wrapper {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          z-index: 10;
        }

        .line1 {
          color: #ffffff;
          font-size: 76px;
          font-weight: 700;
          letter-spacing: -0.01em;
          margin-bottom: 24px;
        }

        .divider {
          width: 800px; /* An elegant thin divider spanning underneath */
          height: 1px;
          background-color: #334155;
          margin-bottom: 40px;
        }

        .line2 {
          color: #ffffff;
          font-size: 56px;
          font-weight: 700;
          margin-bottom: 36px;
          letter-spacing: 0.06em;
        }

        .line3 {
          color: #85a7bd;
          font-size: 48px;
          font-weight: 600;
          letter-spacing: 0.04em;
        }
      </style>
    </head>
    <body>
      <div class="center-hex">
        <svg viewBox="0 0 450 450" fill="none" stroke="#ffffff" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg">
          <path d="M225,56 L375,142 L375,308 L225,394 L75,308 L75,142 Z" />
          <path d="M225,56 L225,394" opacity="0.3" />
          <path d="M75,142 L375,308" opacity="0.3" />
          <path d="M75,308 L375,142" opacity="0.3" />
        </svg>
      </div>
      <div class="hex-pattern">
        <svg viewBox="0 0 800 800" fill="none" stroke="#ffffff" stroke-width="2" xmlns="http://www.w3.org/2000/svg">
          <!-- Geometric Hexagon Network -->
          <path d="M400,200 L550,286 L550,459 L400,545 L250,459 L250,286 Z" />
          <path d="M250,459 L250,632 L100,718 L-50,632 L-50,459 L100,373 Z" />
          <path d="M100,373 L250,286 L250,113 L100,27 L-50,113 L-50,286 Z" />
          <path d="M550,459 L700,545 L700,718 L550,804 L400,718 L400,545 Z" />
          <path d="M550,113 L700,200 L700,373 L550,459 L400,373 L400,200 Z" />
          <!-- Inner details for tech feel -->
          <circle cx="400" cy="545" r="8" fill="#ffffff" />
          <circle cx="550" cy="459" r="8" fill="#ffffff" />
          <circle cx="250" cy="459" r="8" fill="#ffffff" />
          <circle cx="550" cy="286" r="8" fill="#ffffff" />
          <circle cx="250" cy="286" r="8" fill="#ffffff" />
          <path d="M400,200 L400,100" />
          <path d="M400,545 L400,645" />
          <path d="M550,459 L620,500" />
          <path d="M250,459 L180,500" />
        </svg>
      </div>

      <div class="content-wrapper">
        <div class="line1">Next.js / Stripe</div>
        <div class="divider"></div>
        <div class="line2">不具合診断・修正します</div>
        <div class="line3">Webhook・API連携対応</div>
      </div>
    </body>
    </html>
  `;
  await page.setContent(html);
  
  // Wait for fonts to load properly
  await page.evaluate(async () => {
    await document.fonts.ready;
  });

  await page.screenshot({ path: '/home/hr-hm/Project/work/banner_v2.png' });
  await browser.close();
})();
