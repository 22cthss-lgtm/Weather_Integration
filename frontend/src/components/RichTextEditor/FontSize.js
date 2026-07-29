export const FONT_SIZES = ["12px", "14px", "16px", "18px", "20px", "24px", "28px", "32px"];

export function isAllowedFontSize(value) {
  return FONT_SIZES.includes(value);
}
