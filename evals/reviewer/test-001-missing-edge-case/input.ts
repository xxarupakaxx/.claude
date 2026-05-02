// 文字列パース関数のテスト（エッジケース欠落例）
import { describe, it, expect } from "vitest";
import { parsePositiveInteger } from "./parser";

// テスト対象実装（src/parser.ts として想定）
//   export function parsePositiveInteger(input: string): number {
//     const n = Number(input);
//     if (!Number.isInteger(n) || n <= 0) {
//       throw new Error(`Invalid positive integer: ${input}`);
//     }
//     return n;
//   }

describe("parsePositiveInteger", () => {
  it("正の整数文字列を変換できる", () => {
    expect(parsePositiveInteger("42")).toBe(42);
  });

  it("文字列の '1' を 1 として返す", () => {
    expect(parsePositiveInteger("1")).toBe(1);
  });

  // エッジケース欠落:
  // - 空文字列 ""
  // - 負の数 "-5"
  // - 0
  // - 小数 "3.14"
  // - 16進数 "0x10"
  // - 先頭/末尾のスペース " 42 "
  // - 非数字 "abc"
  // - Number.MAX_SAFE_INTEGER 超過
  // - 全角数字 "４２"
  // - null / undefined（型違反だが実行時挙動は？）
});
