--
-- PostgreSQL database dump
--

--
-- Name: orders; Type: TABLE; Schema: public; Owner: devuser
--

DROP TABLE IF EXISTS "orders";

CREATE TABLE "orders" (
  "order_id" SERIAL PRIMARY KEY,
  "user_id" integer,
  "product_name" varchar(100) NOT NULL,
  "amount" decimal(10,2) NOT NULL,
  "order_date" date
);

ALTER TABLE "orders" OWNER TO devuser;

COMMENT ON COLUMN "orders"."order_id" IS '주문 번호';
COMMENT ON COLUMN "orders"."user_id" IS '사용자 ID';
COMMENT ON COLUMN "orders"."product_name" IS '상품명';
COMMENT ON COLUMN "orders"."amount" IS '주문 금액';
COMMENT ON COLUMN "orders"."order_date" IS '주문일';

--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: devuser
--

INSERT INTO "orders" VALUES (1,1,'노트북',1500000.00,'2024-07-01'),(2,2,'기계식 키보드',120000.00,'2024-07-03'),(3,1,'무선 마우스',35000.00,'2024-07-05'),(4,3,'집현전 대형 책상',250000.00,'2024-07-10'),(5,2,'거북선 모양 USB',25000.00,'2024-07-12');

--
-- Name: orders_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: devuser
--

ALTER TABLE ONLY "orders"
    ADD CONSTRAINT "orders_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"(id);


--
-- Name: idx_orders_user_id; Type: INDEX; Schema: public; Owner: devuser
--

CREATE INDEX "idx_orders_user_id" ON "orders" USING btree ("user_id");


--
-- PostgreSQL database dump complete
--
