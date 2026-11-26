
import fs from "node:fs";
import path from "node:path";

// 1. Vercel 환경 변수에서 백엔드 URL 읽기
const apiBaseUrl = process.env.API_BASE_URL;

if (!apiBaseUrl) {
  throw new Error("API_BASE_URL 환경 변수가 설정되지 않았습니다.");
}

// 2. API 주소 유효성 확인
const url = new URL(apiBaseUrl);

if (url.protocol !== "https:") {
  throw new Error("API_BASE_URL은 HTTPS 주소여야 합니다.");
}

// 3. 배포 파일 폴더 생성
const outputDir = path.resolve("dist");

fs.mkdirSync(outputDir, { recursive: true });

// 4. HTML, CSS, JavaScript 파일 복사
for (const file of ["index.html", "style.css", "app.js"]) {
  fs.copyFileSync(file, path.join(outputDir, file));
}

// 5. 환경 변수를 반영한 config.js 생성
const config = {
  API_BASE_URL: apiBaseUrl.replace(/\/$/, "")
};

fs.writeFileSync(
  path.join(outputDir, "config.js"),
  `window.APP_CONFIG = ${JSON.stringify(config)};\n`,
  "utf8"
);

console.log("Frontend build completed.");
console.log("API Base URL:", config.API_BASE_URL);
