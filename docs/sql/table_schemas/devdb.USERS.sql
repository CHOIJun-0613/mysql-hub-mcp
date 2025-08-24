DROP TABLE IF EXISTS "users";

CREATE TABLE "users" (
    id integer NOT NULL,
    user_name character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    signup_date date
);

ALTER TABLE "users" OWNER TO devuser;

-- 테이블블 코멘트 추가
COMMENT ON TABLE "users" IS '사용자 테이블';

-- 컬럼 코멘트 추가 (id, user_name, email, signup_date)
COMMENT ON COLUMN "users"."id" IS '사용자 ID';
COMMENT ON COLUMN "users"."user_name" IS '사용자 이름';
COMMENT ON COLUMN "users"."email" IS '이메일';
COMMENT ON COLUMN "users"."signup_date" IS '가입일';


-- 인덱스 추가
CREATE INDEX idx_users_email ON "users" (email);

-- 제약조건 추가
ALTER TABLE "users" ADD CONSTRAINT users_email_unique UNIQUE (email);

