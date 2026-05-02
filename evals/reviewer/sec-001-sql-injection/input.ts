// User search API (TypeScript / Express)
import express, { Request, Response } from "express";
import { db } from "./db";

export async function searchUsers(req: Request, res: Response) {
  const { name } = req.query;

  // 検索クエリを動的SQL文字列で組み立てる（脆弱）
  const query = `SELECT id, email, name FROM users WHERE name LIKE '%${name}%'`;
  const rows = await db.raw(query);

  res.json(rows);
}

export async function getUserById(req: Request, res: Response) {
  const { id } = req.params;

  // ユーザー入力を直接 SQL に埋め込む（脆弱）
  const sql = "SELECT * FROM users WHERE id = " + id;
  const row = await db.raw(sql);

  res.json(row);
}

export async function deleteUser(req: Request, res: Response) {
  const { id } = req.body;

  // 入力検証なし（may_detect）
  await db.raw(`DELETE FROM users WHERE id = ${id}`);

  res.status(204).end();
}
