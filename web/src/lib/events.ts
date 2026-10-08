import rawEvents from '../data/events.json';

/** 与 `pipeline/normalizer.py` 导出的字段一一对应，不新增、不改写字段语义。 */
export interface EventItem {
  id: string;
  sourceType: string;
  sourceName: string;
  title: string;
  category: string;
  city: string;
  venue: string;
  startDate: string;
  endDate: string | null;
  priceRange: string | null;
  ticketUrl: string | null;
  imageUrl: string | null;
  status: string;
  confidence: number;
  canonicalId: string | null;
  scrapedAt: string | null;
}

export const records = rawEvents as unknown as EventItem[];

/* ------------------------------------------------------------------ *
 * 时间：抓取数据使用 Asia/Shanghai 的日历日（YYYY-MM-DD 字符串），
 * 全程按字符串比较，避免构建机时区（CI/Vercel 为 UTC）造成偏移。
 * ------------------------------------------------------------------ */

export const TODAY = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Shanghai',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
}).format(new Date());

const DAY_MS = 86_400_000;
const utc = (iso: string) => Date.parse(`${iso}T00:00:00Z`);
const WEEKDAY = ['日', '一', '二', '三', '四', '五', '六'];

export type Phase = 'ongoing' | 'upcoming' | 'past';

/** 单日活动当天视为进行中；跨日活动按结束日判断。 */
export function phaseOf(e: EventItem): Phase {
  const end = e.endDate ?? e.startDate;
  if (end < TODAY) return 'past';
  return e.startDate <= TODAY ? 'ongoing' : 'upcoming';
}

export function daysFromToday(iso: string): number {
  return Math.round((utc(iso) - utc(TODAY)) / DAY_MS);
}

export const SOURCE_SHORT: Record<string, string> = {
  bilibili: 'B 站会员购',
  weibo: '微博',
};

export const sourceShort = (name: string) => SOURCE_SHORT[name] ?? name;

export function relativeLabel(iso: string): string {
  const d = daysFromToday(iso);
  if (d === 0) return '就在今天';
  if (d === 1) return '明天开始';
  if (d > 1) return `${d} 天后开始`;
  if (d === -1) return '昨天开始';
  return `${-d} 天前开始`;
}

/** 结合阶段的人话时间说明：进行中的活动不说「N 天前开始」。 */
export function phaseNote(e: EventItem): string {
  const phase = phaseOf(e);
  if (phase === 'past') return `已结束 · ${fullDate(e.endDate ?? e.startDate)}`;
  if (phase === 'ongoing') {
    const day = 1 - daysFromToday(e.startDate);
    return day <= 1 ? '今天开始' : `进行中 · 第 ${day} 天`;
  }
  return relativeLabel(e.startDate);
}

export function dateParts(iso: string) {
  const [y, m, d] = iso.split('-').map(Number);
  return { y, m, d, weekday: `周${WEEKDAY[new Date(utc(iso)).getUTCDay()]}` };
}

export const fullDate = (iso: string) => {
  const p = dateParts(iso);
  return `${p.y} 年 ${p.m} 月 ${p.d} 日`;
};

export const shortDate = (iso: string) => {
  const p = dateParts(iso);
  return `${p.m} 月 ${p.d} 日`;
};

export function rangeLabel(e: EventItem): string {
  if (!e.endDate || e.endDate === e.startDate) return fullDate(e.startDate);
  return `${fullDate(e.startDate)} – ${fullDate(e.endDate)}`;
}

export const monthKey = (iso: string) => iso.slice(0, 7);

export function monthLabel(key: string): string {
  const [y, m] = key.split('-').map(Number);
  return `${y} 年 ${m} 月`;
}

/* ------------------------------------------------------------------ *
 * 文本展示规范化：只折叠空白，不删改任何字符。
 * 社交平台抓取的标题常带换行与缩进，首行作为标题、其余作为摘要原文。
 * ------------------------------------------------------------------ */

const collapse = (s: string) => s.replace(/\s+/g, ' ').trim();

export function titleParts(e: EventItem) {
  const normalized = e.title.replace(/\r/g, '');
  const cut = normalized.indexOf('\n');
  const headline = collapse(cut === -1 ? normalized : normalized.slice(0, cut));
  const rest = collapse(cut === -1 ? '' : normalized.slice(cut + 1));
  return { headline: headline || collapse(normalized), excerpt: rest, full: collapse(normalized) };
}

/* ------------------------------------------------------------------ *
 * 来源与可信度：直接来自数据的 sourceType / sourceName / confidence，
 * 不做推断。票务平台字段来自结构化接口；社交平台来自公开动态。
 * ------------------------------------------------------------------ */

const SOURCE_LABEL: Record<string, string> = {
  bilibili: '哔哩哔哩会员购',
  weibo: '微博',
};

export const sourceLabel = (name: string) => SOURCE_LABEL[name] ?? name;

export interface Reliability {
  key: 'verified' | 'unverified';
  label: string;
  short: string;
  note: string;
}

export const RELIABILITY_NOTE = {
  verified: '字段来自票务平台结构化接口，含购票链接与场次价格。',
  unverified: '来自社交平台公开动态的自动识别结果，城市、场地与场次可能不准确。',
} as const;

export function reliabilityOf(e: EventItem): Reliability {
  return e.sourceType === 'ticketing'
    ? { key: 'verified', label: '票务平台核验', short: '核验', note: RELIABILITY_NOTE.verified }
    : { key: 'unverified', label: '未经核验', short: '未核验', note: RELIABILITY_NOTE.unverified };
}

export const cityLabel = (e: EventItem) => e.city || '城市待确认';

/** 社交来源的 venue 字段常是动态正文碎片，不足以作为场地展示。 */
export function venueLabel(e: EventItem): string | null {
  if (e.sourceType !== 'ticketing') return null;
  return e.venue ? collapse(e.venue) : null;
}

export function priceLabel(e: EventItem): string | null {
  if (!e.priceRange || e.priceRange === '待定') return null;
  return e.priceRange;
}

export const scraperLabel = (e: EventItem) => sourceLabel(e.sourceName);

/* ------------------------------------------------------------------ *
 * 分类配色：产品自身的色彩分配（品牌八色之一），只用于分类区分。
 * 未在表中的分类回退到 Steel，并且仍然可以正常展示。
 * ------------------------------------------------------------------ */

interface CategoryMeta {
  slug: string;
  color: string;
  en: string;
}

const CATEGORY_META: Record<string, CategoryMeta> = {
  漫展: { slug: 'manzhan', color: 'var(--dn-teal)', en: 'COMIC CON' },
  同人展: { slug: 'doujin', color: 'var(--dn-violet)', en: 'DOUJIN FAIR' },
  演唱会: { slug: 'concert', color: 'var(--dn-orange)', en: 'CONCERT' },
  音乐会: { slug: 'music', color: 'var(--dn-amber)', en: 'ORCHESTRA' },
  展览: { slug: 'exhibition', color: 'var(--dn-cyan)', en: 'EXHIBITION' },
  其他: { slug: 'other', color: 'var(--dn-steel)', en: 'OTHER' },
};

export const categoryColor = (c: string) => CATEGORY_META[c]?.color ?? 'var(--dn-steel)';
export const categoryEn = (c: string) => CATEGORY_META[c]?.en ?? 'OTHER';
export const categorySlug = (c: string) => CATEGORY_META[c]?.slug ?? encodeURIComponent(c);

/* ------------------------------------------------------------------ *
 * 集合视图
 * ------------------------------------------------------------------ */

export interface EventGroup {
  key: string;
  rep: EventItem;
  /** 同源重复记录数（含代表记录）。数据源中确实存在，此处如实呈现而非隐藏。 */
  copies: number;
}

/** 按「来源 + 开始日 + 分类 + 标题」折叠同源重复记录，不丢弃任何记录。 */
export function groupEvents(list: EventItem[]): EventGroup[] {
  const map = new Map<string, EventGroup>();
  for (const e of list) {
    const key = `${e.sourceName}|${e.startDate}|${e.category}|${collapse(e.title)}`;
    const hit = map.get(key);
    if (hit) hit.copies += 1;
    else map.set(key, { key, rep: e, copies: 1 });
  }
  return [...map.values()];
}

const byStart = (a: EventItem, b: EventItem) => a.startDate.localeCompare(b.startDate);

export const ongoing = records.filter((e) => phaseOf(e) === 'ongoing').sort(byStart);
export const upcoming = records.filter((e) => phaseOf(e) === 'upcoming').sort(byStart);
export const past = records.filter((e) => phaseOf(e) === 'past').sort((a, b) => -byStart(a, b));

export interface MonthBucket {
  key: string;
  label: string;
  groups: EventGroup[];
  count: number;
}

export function byMonth(list: EventItem[]): MonthBucket[] {
  const map = new Map<string, EventItem[]>();
  for (const e of list) {
    const key = monthKey(e.startDate);
    const bucket = map.get(key);
    if (bucket) bucket.push(e);
    else map.set(key, [e]);
  }
  return [...map.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([key, items]) => ({
      key,
      label: monthLabel(key),
      groups: groupEvents(items),
      count: items.length,
    }));
}

export interface CityBucket {
  name: string;
  slug: string;
  count: number;
  groups: EventGroup[];
}

/** 城市索引（仅统计已解析出城市的记录），按记录数降序。 */
export function cityBuckets(list: EventItem[] = records): CityBucket[] {
  const map = new Map<string, EventItem[]>();
  for (const e of list) {
    if (!e.city) continue;
    const bucket = map.get(e.city);
    if (bucket) bucket.push(e);
    else map.set(e.city, [e]);
  }
  return [...map.entries()]
    .sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0]))
    .map(([name, items]) => ({
      name,
      slug: citySlug(name),
      count: items.length,
      groups: groupEvents(items.sort(byStart)),
    }));
}

/** 城市名是中文，使用稳定的 ASCII slug 作为路由，避免静态托管的编码差异。 */
export function citySlug(name: string): string {
  const known: Record<string, string> = {
    北京: 'beijing', 上海: 'shanghai', 广州: 'guangzhou', 深圳: 'shenzhen',
    杭州: 'hangzhou', 成都: 'chengdu', 武汉: 'wuhan', 南京: 'nanjing',
    西安: 'xian', 长沙: 'changsha', 天津: 'tianjin', 重庆: 'chongqing',
    厦门: 'xiamen', 南昌: 'nanchang', 郑州: 'zhengzhou', 东莞: 'dongguan',
    温州: 'wenzhou', 烟台: 'yantai', 石家庄: 'shijiazhuang', 沙田区: 'shatian',
  };
  if (known[name]) return known[name];
  // 兜底：由字符码生成稳定 slug，保证新城市不会破坏静态路由。
  return `c${[...name].map((ch) => ch.codePointAt(0)!.toString(16)).join('')}`;
}

export interface CategoryBucket {
  name: string;
  slug: string;
  color: string;
  en: string;
  count: number;
  upcomingCount: number;
}

export function categoryBuckets(list: EventItem[] = records): CategoryBucket[] {
  const map = new Map<string, EventItem[]>();
  for (const e of list) {
    const bucket = map.get(e.category);
    if (bucket) bucket.push(e);
    else map.set(e.category, [e]);
  }
  return [...map.entries()]
    .sort((a, b) => b[1].length - a[1].length)
    .map(([name, items]) => ({
      name,
      slug: categorySlug(name),
      color: categoryColor(name),
      en: categoryEn(name),
      count: items.length,
      upcomingCount: items.filter((e) => phaseOf(e) !== 'past').length,
    }));
}

export interface SourceBucket {
  name: string;
  label: string;
  sourceType: string;
  count: number;
  note: string;
}

export function sourceBuckets(list: EventItem[] = records): SourceBucket[] {
  const map = new Map<string, EventItem[]>();
  for (const e of list) {
    const bucket = map.get(e.sourceName);
    if (bucket) bucket.push(e);
    else map.set(e.sourceName, [e]);
  }
  return [...map.entries()]
    .sort((a, b) => b[1].length - a[1].length)
    .map(([name, items]) => ({
      name,
      label: sourceLabel(name),
      sourceType: items[0].sourceType,
      count: items.length,
      note: reliabilityOf(items[0]).note,
    }));
}

/* ------------------------------------------------------------------ *
 * 数据快照：全部数值来自数据本身，缺失时明确为 null，不虚构。
 * ------------------------------------------------------------------ */

export interface Snapshot {
  total: number;
  ongoing: number;
  upcoming: number;
  past: number;
  next30: number;
  onSale: number;
  forecast: number;
  withTicketUrl: number;
  withCity: number;
  cityCount: number;
  duplicateRecords: number;
  pendingScrapedAt: string | null;
}

function buildSnapshot(): Snapshot {
  const stamped = records
    .map((e) => e.scrapedAt)
    .filter((s): s is string => Boolean(s))
    .sort();
  const groups = groupEvents(records);
  return {
    total: records.length,
    ongoing: ongoing.length,
    upcoming: upcoming.length,
    past: past.length,
    next30: records.filter(
      (e) => phaseOf(e) !== 'past' && daysFromToday(e.startDate) >= 0 && daysFromToday(e.startDate) <= 30,
    ).length,
    onSale: records.filter((e) => e.status === '售票中' && phaseOf(e) !== 'past').length,
    forecast: records.filter((e) => e.status === '预告' && phaseOf(e) !== 'past').length,
    withTicketUrl: records.filter((e) => e.ticketUrl && phaseOf(e) !== 'past').length,
    withCity: records.filter((e) => e.city).length,
    cityCount: cityBuckets().length,
    duplicateRecords: groups.reduce((n, g) => n + (g.copies - 1), 0),
    pendingScrapedAt: stamped.at(-1) ?? null,
  };
}

export const snapshot: Snapshot = buildSnapshot();

/** scraped_at 在 db/schema.py 中以 UTC 无时区浮点存库，此处按 UTC 读取并给出北京时间。 */
export function snapshotTimes(iso: string | null): { utc: string; cst: string } | null {
  if (!iso) return null;
  const parsed = new Date(`${iso}Z`);
  if (Number.isNaN(parsed.getTime())) return null;
  const cst = parsed.toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
  return { utc: `${iso.slice(0, 19).replace('T', ' ')} UTC`, cst: `${cst}（北京）` };
}

/** 入场交错索引上限：长列表不让最后一项等待数秒。 */
export const enterIndex = (i: number) => Math.min(i, 8);
