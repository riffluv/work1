const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Noto+Sans+JP:wght@400;500;700;900&display=swap');
    
    body {
      margin: 0;
      padding: 0;
      width: 1220px;
      height: 1016px;
      margin: 0;
      background: linear-gradient(135deg, #0d1b2a 0%, #162d3e 100%);
      font-family: 'Inter', 'Noto Sans JP', sans-serif;
      position: relative;
      overflow: hidden;
    }

    /* 右側のヘキサゴン・ネットワークパターン（透過率8%） */
    .hexagon-pattern {
      position: absolute;
      top: 0;
      right: 0;
      width: 800px;
      height: 1280px;
      background-image: url("data:image/svg+xml,%3Csvg width='60' height='103.92304845413263' viewBox='0 0 60 103.92304845413263' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 0l30 17.32050807568877v34.64101615137754L30 69.28203230275508 0 51.96152422706631V17.32050807568877L30 0zm0 34.64101615137754L15 25.980762113533157v-17.32050807568877L30 0l15 8.660254037844386v17.32050807568877L30 34.64101615137754zM0 86.60254037844385V51.96152422706631L30 69.28203230275508l30-17.32050807568877v34.64101615137754l-30 17.32050807568877L0 86.60254037844385z' fill='%23ffffff' fill-opacity='0.1' fill-rule='evenodd'/%3E%3C/svg%3E");
      -webkit-mask-image: linear-gradient(to right, transparent, black);
      opacity: 0.6; /* svg自体の0.1 * 0.6 = 実質6%の濃さ */
      z-index: 1;
    }

    /* 光のフレア（左上と右下から微かな光） */
    .glow-top-left {
      position: absolute;
      top: -300px;
      left: -300px;
      width: 800px;
      height: 800px;
      background: radial-gradient(circle, rgba(56, 189, 248, 0.12) 0%, transparent 70%);
      z-index: 2;
    }
    
    .glow-bottom-right {
      position: absolute;
      bottom: -400px;
      right: -200px;
      width: 1000px;
      height: 1000px;
      background: radial-gradient(circle, rgba(99, 102, 241, 0.08) 0%, transparent 70%);
      z-index: 2;
    }

    /* メインコンテンツラップ */
    .content-wrapper {
      position: absolute;
      top: 0;
      left: 0;
      width: 1220px;
      height: 1016px;
      padding: 160px 180px;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      justify-content: center;
      z-index: 10;
    }

    .subtitle-wrapper {
      display: flex;
      align-items: center;
      margin-bottom: 40px;
    }

    .tech-tag {
      color: #94a3b8; /* Tailwind slate-400 */
      font-size: 38px;
      font-weight: 600;
      letter-spacing: 0.08em;
      border: 1px solid rgba(148, 163, 184, 0.3);
      padding: 12px 32px;
      border-radius: 8px;
      background: rgba(15, 23, 42, 0.4);
      backdrop-filter: blur(4px);
    }

    .main-heading {
      color: #ffffff;
      font-size: 92px;
      font-weight: 900;
      line-height: 1.3;
      letter-spacing: 0.03em;
      margin-bottom: 60px;
    }

    /* エレガントなディバイダー */
    .divider {
      width: 140px;
      height: 4px;
      background: linear-gradient(90deg, #38bdf8, #818cf8);
      border-radius: 2px;
      margin-bottom: 110px;
    }

    /* リストアイテム */
    .symptom-list {
      display: flex;
      flex-direction: column;
      gap: 56px;
    }

    .list-item {
      display: flex;
      align-items: center;
      background: linear-gradient(90deg, rgba(255,255,255,0.03) 0%, transparent 100%);
      padding: 24px 32px;
      border-left: 4px solid rgba(255, 255, 255, 0.1);
      border-radius: 0 12px 12px 0;
      transition: all 0.3s ease;
    }

    .check-icon-wrapper {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 64px;
      height: 64px;
      background: rgba(56, 189, 248, 0.15);
      border-radius: 50%;
      margin-right: 40px;
      border: 1px solid rgba(56, 189, 248, 0.3);
      box-shadow: 0 0 20px rgba(56, 189, 248, 0.2);
    }

    .check-icon {
      color: #38bdf8;
      font-size: 36px;
      font-weight: 900;
    }

    .list-text {
      color: #f8fafc;
      font-size: 46px;
      font-weight: 700;
      letter-spacing: 0.04em;
    }
  </style>
</head>
<body>
  <div class="hexagon-pattern"></div>
  <div class="glow-top-left"></div>
  <div class="glow-bottom-right"></div>
  
  <div class="content-wrapper">
    <div class="subtitle-wrapper">
      <div class="tech-tag">Next.js / Stripe</div>
    </div>
    
    <div class="main-heading">
      こんな症状に対応
    </div>
    
    <div class="divider"></div>
    
    <div class="symptom-list">
      <div class="list-item">
        <div class="check-icon-wrapper">
          <div class="check-icon">✓</div>
        </div>
        <div class="list-text">決済は通るのに、アプリ側に反映されない</div>
      </div>
      
      <div class="list-item">
        <div class="check-icon-wrapper">
          <div class="check-icon">✓</div>
        </div>
        <div class="list-text">本番環境でだけWebhookが失敗する</div>
      </div>
      
      <div class="list-item">
        <div class="check-icon-wrapper">
          <div class="check-icon">✓</div>
        </div>
        <div class="list-text">Next.jsのAPI処理で500エラーが出る</div>
      </div>
    </div>
  </div>
</body>
</html>
`;

(async () => {
    try {
        console.log('Launching puppeteer...');
        const browser = await puppeteer.launch({
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=none'],
            defaultViewport: {
                width: 1220,
                height: 1016,
                deviceScaleFactor: 2 // より高画質にするためRetina解像度(2x)でキャプチャ
            }
        });
        const page = await browser.newPage();
        
        console.log('Setting HTML content and waiting for fonts...');
        await page.setContent(htmlContent, { waitUntil: 'networkidle0' });
        
        // フォントが適用されるまで確実に待機
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const outputPath = path.join(__dirname, 'thumbnail_coconala_symptoms.png');
        console.log('Taking screenshot...');
        await page.screenshot({ path: outputPath });
        
        await browser.close();
        console.log('Successfully saved to:', outputPath);
    } catch (e) {
        console.error('Error:', e);
    }
})();
