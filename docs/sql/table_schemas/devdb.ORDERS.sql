DROP TABLE IF EXISTS "orders";
CREATE TABLE "orders" (
  "order_id" SERIAL PRIMARY KEY,
  "user_id" integer,
  "product_name" varchar(100) NOT NULL,
  "amount" decimal(10,2) NOT NULL,
  "order_date" date
);

ALTER TABLE "orders" OWNER TO devuser;

-- 테이블블 코멘트 추가
COMMENT ON TABLE "orders" IS '주문 내역';
COMMENT ON COLUMN "orders"."order_id" IS '주문 번호';
COMMENT ON COLUMN "orders"."user_id" IS '사용자 ID';
COMMENT ON COLUMN "orders"."product_name" IS '상품명';
COMMENT ON COLUMN "orders"."amount" IS '주문 금액';
COMMENT ON COLUMN "orders"."order_date" IS '주문일';
