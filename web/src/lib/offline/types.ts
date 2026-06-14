import type { CreateTransactionBody, Transaction } from "@/api/client";

export type QueuedOp =
  | {
      id: string;
      type: "createTransaction";
      createdAt: number;
      tempId: string;
      body: CreateTransactionBody;
    }
  | {
      id: string;
      type: "deleteTransaction";
      createdAt: number;
      transactionId: string;
    }
  | {
      id: string;
      type: "createAccount";
      createdAt: number;
      tempId: string;
      body: { name: string; balance: number };
    }
  | {
      id: string;
      type: "deleteAccount";
      createdAt: number;
      accountId: string;
    }
  | {
      id: string;
      type: "updateTransactionItem";
      createdAt: number;
      transactionId: string;
      itemId: string;
      categoryId: string;
    };

export type LocalTransaction = Transaction & {
  _local?: true;
  _pending?: true;
  title?: string;
};

export type CacheEntry<T> = {
  data: T;
  fetchedAt: number;
};
