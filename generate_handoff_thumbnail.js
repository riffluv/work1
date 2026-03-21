const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1220, height: 1016 });
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
          width: 1220px;
          height: 1016px;
          background: linear-gradient(to right, #1A2430, #2B3D4D);
          font-family: 'Inter', 'Noto Sans JP', sans-serif;
          overflow: hidden;
          position: relative;
        }

        .hex-pattern {
          position: absolute;
          top: 0;
          right: -50px;
          width: 600px;
          height: 1016px;
          opacity: 0.035;
          z-index: 1;
          pointer-events: none;
          -webkit-mask-image: linear-gradient(to right, rgba(0,0,0,0) 0%, rgba(0,0,0,1) 100%);
          mask-image: linear-gradient(to right, rgba(0,0,0,0) 0%, rgba(0,0,0,1) 100%);
        }

        .content-wrapper {
          position: absolute;
          top: 50%;
          left: 52%;
          transform: translate(-50%, -50%);
          width: max-content;
          height: auto;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: flex-start;
          z-index: 10;
        }

        .line1 {
          color: #ffffff;
          font-size: 56px;
          font-weight: 700;
          letter-spacing: 0.03em;
          margin-bottom: 40px;
        }

        .line2 {
          color: #ffffff;
          font-size: 92px;
          font-weight: 700;
          letter-spacing: 0.05em;
          margin-bottom: 45px;
          white-space: nowrap;
          text-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .line3 {
          color: #A7BAC8;
          font-size: 42px;
          font-weight: 700;
          letter-spacing: 0.04em;
          white-space: nowrap;
          text-shadow: 0 3px 8px rgba(0, 0, 0, 0.15);
        }
      </style>
    </head>
    <body>
      <div class="hex-pattern">
        <svg viewBox="0 0 600 1016" fill="none" stroke="#ffffff" stroke-width="2" xmlns="http://www.w3.org/2000/svg">
          <pattern id="hexagons" width="100" height="173.2" patternUnits="userSpaceOnUse">
            <path d="M50,0 L100,28.87 L100,86.6 L50,115.47 L0,86.6 L0,28.87 Z" />
            <path d="M50,173.2 L100,144.33 L100,86.6" />
          </pattern>
          <rect width="100%" height="100%" fill="url(#hexagons)" />
        </svg>
      </div>

      <div class="content-wrapper">
        <div class="line1">AI / 外注コード</div>
        <div class="line2">主要な流れを1つ整理</div>
        <div class="line3">引き継ぎメモを作成</div>
      </div>
    </body>
    </html>
  `;
  await page.setContent(html);
  
  await page.evaluate(async () => {
    await document.fonts.ready;
  });

  await page.screenshot({ path: '/home/hr-hm/Project/work/thumbnail_coconala_handoff.png' });
  await browser.close();
})();
