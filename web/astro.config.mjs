// @ts-check
import { defineConfig } from 'astro/config';

// ComiRadar 独立站：数据由 anime-con-radar 每日抓取后提交到 web/src/data/events.json
export default defineConfig({
  site: 'https://comi.dreamnight.net.cn',
});