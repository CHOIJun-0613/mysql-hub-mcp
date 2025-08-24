-- =================================================================
-- 표준 용어 테이블 (STND_TERM) 생성 (PostgreSQL)
-- : 표준 단어의 조합으로 구성된 '업무 용어'를 관리합니다.
-- =================================================================

-- 테이블이 이미 존재할 경우 삭제 (필요시 사용)
-- DROP TABLE IF EXISTS STND_TERM;

CREATE TABLE STND_TERM (
    TERM_NM VARCHAR(200) NOT NULL,
    TERM_ENG_NM VARCHAR(200) NOT NULL,
    TERM_DESC VARCHAR(500) NULL,
    TERM_ENG_ABR_NM VARCHAR(100) NOT NULL,
    PRIMARY KEY (TERM_NM)
);

-- 테이블 및 컬럼 코멘트 추가
COMMENT ON TABLE STND_TERM IS '표준 용어';
COMMENT ON COLUMN STND_TERM.TERM_NM IS '용어명 (한글)';
COMMENT ON COLUMN STND_TERM.TERM_ENG_NM IS '용어 영문명';
COMMENT ON COLUMN STND_TERM.TERM_DESC IS '용어 설명';
COMMENT ON COLUMN STND_TERM.TERM_ENG_ABR_NM IS '용어 영문 약어명 (단어약어_단어약어)';

-- =================================================================
-- 표준 용어 데이터 삽입 (PostgreSQL)
-- =================================================================

-- 고객 관련 용어 (Customer-related Terms)
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('고객번호', 'Customer Number', '고객을 식별하기 위해 은행이 부여하는 고유 번호', 'CUST_NO');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('고객등급', 'Customer Grade', '고객의 거래 기여도, 신용도 등을 종합하여 산정한 등급', 'CUST_GRD');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('개인고객', 'Individual Customer', '개인 자격으로 은행과 거래하는 고객', 'INDV_CUST');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('법인고객', 'Corporate Customer', '기업, 기관 등 법인 자격으로 은행과 거래하는 고객', 'CORP_CUST');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('실명번호', 'Real Name Number', '주민등록번호 또는 사업자등록번호와 같이 법적으로 실명을 확인할 수 있는 번호', 'REAL_NM_NO');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('고객정보', 'Customer Information', '고객의 신원, 연락처, 거래 정보 등을 포함하는 데이터', 'CUST_INFO');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('비밀번호', 'Password', '본인 확인을 위해 사용하는 문자, 숫자 등의 조합', 'PW');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('고객상태', 'Customer Status', '고객의 현재 상태(정상, 휴면, 거래중지 등)', 'CUST_STAT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('고객확인', 'Customer Verification', '금융실명법 및 AML 규정에 따라 고객의 신원을 확인하는 절차', 'CUST_VERI');

-- 계좌/예금 관련 용어 (Account/Deposit-related Terms)
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('계좌번호', 'Account Number', '특정 계좌를 식별하기 위한 고유 번호', 'ACCT_NO');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('계좌상태', 'Account Status', '계좌의 현재 상태(정상, 해지, 지급정지 등)', 'ACCT_STAT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('계좌잔액', 'Account Balance', '특정 시점의 계좌에 남아있는 금액', 'ACCT_BAL');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('지급정지', 'Stop Payment', '분실, 도난 등의 사유로 계좌의 출금 거래를 정지시키는 조치', 'PAY_STOP');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('보통예금', 'Savings Deposit', '입출금이 자유로운 요구불예금의 한 종류', 'SVGS_DEPO');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('정기예금', 'Time Deposit', '일정 기간 돈을 예치하고 만기일에 원리금을 받는 거치식 예금', 'TIME_DEPO');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('정기적금', 'Installment Savings', '계약 기간 동안 매월 일정 금액을 납입하여 목돈을 마련하는 적립식 예금', 'INST_SVGS');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('만기일자', 'Maturity Date', '예금, 대출 등의 계약이 종료되는 날짜', 'MTRT_DT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('신규일자', 'New Date', '계좌, 대출 등을 처음 개설하거나 실행한 날짜', 'NEW_DT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('해지일자', 'Termination Date', '금융 계약을 종료한 날짜', 'TERM_DT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('예금잔액', 'Deposit Balance', '예금 계좌에 남아있는 금액', 'DEPO_BAL');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('계좌비밀번호', 'Account Password', '계좌에 접근하기 위한 비밀번호', 'ACCT_PW');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('출금계좌', 'Withdrawal Account', '자금이 빠져나가는 계좌', 'WDRW_ACCT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('입금계좌', 'Deposit Account', '자금이 들어오는 계좌', 'CDEP_ACCT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('이자금액', 'Interest Amount', '원금에 대해 약정된 이율에 따라 발생한 금액', 'INT_AMT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('원금금액', 'Principal Amount', '이자를 발생시키는 최초의 예금액 또는 대출금', 'PRIN_AMT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('휴면계좌', 'Dormant Account', '장기간 거래가 없어 거래가 정지된 계좌', 'DRMT_ACCT');

-- 대출/여신 관련 용어 (Loan/Credit-related Terms)
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('신용대출', 'Credit Loan', '고객의 신용을 바탕으로 담보 없이 실행되는 대출', 'CRD_LOAN');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('주택담보대출', 'House Mortgage Loan', '주택을 담보로 제공하고 받는 대출', 'HOUS_MRT_LOAN');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('대출계좌', 'Loan Account', '대출 거래를 관리하는 계좌', 'LOAN_ACCT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('대출한도', 'Loan Limit', '고객에게 대출해 줄 수 있는 최대 금액', 'LOAN_LIM');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('대출금리', 'Loan Interest Rate', '대출 원금에 대해 부과되는 이자율', 'LOAN_IRT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('기준금리', 'Base Rate', '대출금리를 정할 때 기준이 되는 금리', 'BASE_IRT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('가산금리', 'Spread Rate', '기준금리에 신용도 등을 반영하여 추가로 더하는 금리', 'SPRD_IRT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('연체이자', 'Overdue Interest', '연체된 원리금에 대하여 부과되는 이자', 'OVD_INT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('연체원금', 'Overdue Principal', '상환일이 지났으나 아직 상환되지 않은 원금', 'OVD_PRIN');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('대출잔액', 'Loan Balance', '상환해야 할 대출 원금이 남아있는 금액', 'LOAN_BAL');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('중도상환', 'Midway Repayment', '대출 만기 이전에 원금의 일부 또는 전부를 갚는 것', 'MID_REPY');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('거치기간', 'Grace Period', '대출 실행 후 이자만 납부하고 원금 상환은 유예하는 기간', 'GRAC_PRD');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('상환방식', 'Repayment Method', '대출 원리금을 상환하는 방식(원리금균등, 원금균등 등)', 'REPY_MTHD');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('담보대출', 'Collateral Loan', '부동산, 동산 등의 자산을 담보로 하는 대출', 'COL_LOAN');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('여신한도', 'Credit Limit', '은행이 특정 고객에게 제공할 수 있는 신용공여의 최대 총액', 'CRD_LIM');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('보증금액', 'Guarantee Amount', '보증인이 채무 이행을 책임지는 금액', 'GRNT_AMT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('신용등급', 'Credit Grade', '개인 또는 기업의 신용도를 평가하여 매긴 등급', 'CRD_GRD');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('신용정보', 'Credit Information', '대출, 카드 사용 등 개인의 금융 거래 이력 정보', 'CRD_INFO');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('대출상품', 'Loan Product', '은행에서 판매하는 특정 조건의 대출 패키지', 'LOAN_PROD');

-- 카드 관련 용어 (Card-related Terms)
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('신용카드', 'Credit Card', '신용을 바탕으로 후불 결제하는 카드', 'CRD_CARD');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('체크카드', 'Debit Card', '연결된 계좌에서 즉시 출금되는 카드', 'DEB_CARD');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('카드번호', 'Card Number', '카드를 식별하는 16자리의 고유 번호', 'CARD_NO');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('승인번호', 'Approval Number', '카드 거래가 승인될 때 부여되는 고유 번호', 'APPR_NO');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('카드상태', 'Card Status', '카드의 현재 상태(정상, 분실, 정지 등)', 'CARD_STAT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('결제일자', 'Payment Date', '카드 사용 대금이 계좌에서 출금되는 날짜', 'PAY_DT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('결제금액', 'Payment Amount', '결제일에 납부해야 할 총 카드대금', 'PAY_AMT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('청구금액', 'Billing Amount', '카드사가 회원에게 납부를 요청한 금액', 'BILL_AMT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('할부개월', 'Installment Months', '할부 결제 시 대금을 나누어 내는 개월 수', 'INST_MON');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('현금서비스', 'Cash Advance', '신용카드를 이용해 단기로 현금을 빌리는 서비스', 'CASH_SVC');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('카드한도', 'Card Limit', '신용카드로 사용할 수 있는 최대 금액', 'CARD_LIM');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('가맹점번호', 'Merchant Number', '카드 결제가 가능한 가맹점에 부여된 고유 번호', 'MRCH_NO');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('매입전표', 'Sales Slip', '카드 결제 후 발생하는 매출 기록', 'SALE_SLIP');

-- 거래/채널 관련 용어 (Transaction/Channel-related Terms)
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('거래일자', 'Transaction Date', '금융 거래가 발생한 실제 날짜', 'TRAN_DT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('거래금액', 'Transaction Amount', '거래 시 발생한 금전의 액수', 'TRAN_AMT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('거래유형', 'Transaction Type', '거래의 종류를 나타내는 구분 (입금, 출금, 이체 등)', 'TRAN_TYPE');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('이체수수료', 'Transfer Fee', '계좌 이체 시 발생하는 수수료', 'TRSF_FEE');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('거래내역', 'Transaction History', '특정 기간 동안 발생한 모든 거래의 기록', 'TRAN_HIST');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('자동이체', 'Automatic Transfer', '지정한 날짜에 지정된 금액이 자동으로 이체되는 서비스', 'AUTO_TRSF');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('기산일자', 'Value Date', '이자 계산이 시작되는 기준일', 'VAL_DT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('거래채널', 'Transaction Channel', '거래가 발생한 경로 (영업점, ATM, 인터넷뱅킹 등)', 'TRAN_CHNL');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('영업일자', 'Business Date', '은행이 영업 활동을 하는 날짜', 'BIZ_DT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('인터넷뱅킹', 'Internet Banking', 'PC 인터넷을 통해 금융 서비스를 이용하는 채널', 'IBK');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('모바일뱅킹', 'Mobile Banking', '스마트폰 등 모바일 기기를 통해 금융 서비스를 이용하는 채널', 'MBK');

-- 기타 관리/리스크 용어 (Other Management/Risk Terms)
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('상품코드', 'Product Code', '은행에서 판매하는 금융상품을 식별하기 위한 고유 코드', 'PROD_CODE');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('상품유형', 'Product Type', '금융상품의 종류를 구분하는 카테고리', 'PROD_TYPE');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('수수료코드', 'Fee Code', '각종 수수료를 식별하기 위한 코드', 'FEE_CODE');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('수수료금액', 'Fee Amount', '서비스 제공의 대가로 받는 수수료 액수', 'FEE_AMT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('신용리스크', 'Credit Risk', '거래 상대방의 채무 불이행으로 인해 손실을 입을 위험', 'CRD_RISK');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('시장리스크', 'Market Risk', '주가, 금리, 환율 등 시장 가격의 변동으로 인해 손실을 입을 위험', 'MKT_RISK');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('운영리스크', 'Operational Risk', '부적절한 내부 통제, 시스템 오류 등으로 인해 발생하는 손실 위험', 'OP_RISK');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('유동성리스크', 'Liquidity Risk', '자금 부족으로 인해 만기 도래 채무를 상환하지 못하게 될 위험', 'LQD_RISK');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('시스템코드', 'System Code', '업무 시스템을 구분하는 고유 코드', 'SYS_CODE');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('부서코드', 'Department Code', '은행 내 부서를 식별하기 위한 코드', 'DEPT_CODE');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('직원번호', 'Employee Number', '직원을 식별하기 위한 고유 번호', 'EMP_NO');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('손익계산서', 'Profit and Loss Statement', '일정 기간 동안의 경영 성과를 나타내는 재무제표', 'PL_STMT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('재무상태표', 'Balance Sheet', '특정 시점의 자산, 부채, 자본 상태를 나타내는 재무제표', 'BS_STMT');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('총계정원장', 'General Ledger', '모든 회계 거래를 기록하고 요약한 회계 장부', 'GEN_LDGR');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('계정과목', 'Account Title', '회계 거래를 종류별로 기록하기 위한 명칭', 'ACCT_TTL');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('원천징수', 'Withholding Tax', '소득 지급자가 소득자의 세금을 미리 떼어 국가에 납부하는 제도', 'WHLD_TAX');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('지연배상금', 'Late Fee', '채무 이행을 지체했을 때 부과되는 손해배상금', 'LATE_FEE');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('해외송금', 'Overseas Remittance', '국외로 자금을 이체하는 거래', 'OVS_REMI');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('통화코드', 'Currency Code', '각국 통화를 식별하는 ISO 표준 코드 (KRW, USD 등)', 'CURR_CODE');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('국가코드', 'Country Code', '각국을 식별하는 ISO 표준 코드', 'CNTR_CODE');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('마감처리', 'Closing Process', '일일 거래를 마감하고 정산하는 일련의 과정', 'CLS_PRCS');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('예금보험료', 'Deposit Insurance Premium', '예금자보호법에 따라 은행이 예금보험공사에 납부하는 보험료', 'DEPO_INSU_PREM');
INSERT INTO STND_TERM (TERM_NM, TERM_ENG_NM, TERM_DESC, TERM_ENG_ABR_NM) VALUES ('금융상품', 'Financial Product', '예금, 대출, 펀드 등 은행이 고객에게 제공하는 모든 상품', 'FIN_PROD');

