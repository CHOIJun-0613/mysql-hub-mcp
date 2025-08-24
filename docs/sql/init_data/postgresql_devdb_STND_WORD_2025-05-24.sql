-- =================================================================
-- 표준 단어 테이블 (STND_WORD) 생성 (PostgreSQL)
-- : 업무에서 사용하는 의미의 최소 단위인 '단어'를 관리합니다.
-- =================================================================

-- 테이블이 이미 존재할 경우 삭제 (필요시 사용)
DROP TABLE IF EXISTS STND_WORD;

CREATE TABLE STND_WORD (
    WORD_NM VARCHAR(100) NOT NULL,
    WORD_ENG_NM VARCHAR(100) NOT NULL,
    WORD_DESC VARCHAR(500) NULL,
    WORD_ENG_ABR_NM VARCHAR(20) NOT NULL,
    PRIMARY KEY (WORD_NM)
);

-- 테이블 및 컬럼 코멘트 추가
COMMENT ON TABLE STND_WORD IS '표준 단어';
COMMENT ON COLUMN STND_WORD.WORD_NM IS '단어명 (한글)';
COMMENT ON COLUMN STND_WORD.WORD_ENG_NM IS '단어 영문명';
COMMENT ON COLUMN STND_WORD.WORD_DESC IS '단어 설명';
COMMENT ON COLUMN STND_WORD.WORD_ENG_ABR_NM IS '단어 영문 약어명';


-- =================================================================
-- 표준 단어 데이터 삽입 (PostgreSQL)
-- =================================================================
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('계좌', 'Account', '금융 거래를 기록하고 관리하기 위한 기본 단위', 'ACCT');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('고객', 'Customer', '은행과 금융 거래를 하는 개인 또는 법인 주체', 'CUST');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('금액', 'Amount', '화폐 단위로 표시된 값', 'AMT');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('금리', 'Interest Rate', '원금에 대해 부과되는 이자율', 'IRT');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('기간', 'Period', '정해진 시간의 길이. 시작과 끝이 있는 시간의 간격', 'PRD');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('대출', 'Loan', '은행이 고객에게 자금을 빌려주는 금융 상품', 'LOAN');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('담보', 'Collateral', '채무 변제를 보증하기 위해 제공하는 자산', 'COL');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('등급', 'Grade', '일정한 기준에 따라 매겨진 서열이나 수준', 'GRD');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('마감', 'Closing', '하루의 거래를 정산하여 회계 장부를 마치는 절차', 'CLS');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('만기', 'Maturity', '계약이 종료되어 효력이 발생하는 시점', 'MTRT');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('매입', 'Purchase', '대금을 지급하고 자산이나 권리를 사는 행위', 'PURC');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('번호', 'Number', '대상을 식별하기 위해 부여하는 일련의 숫자나 기호', 'NO');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('법인', 'Corporation', '법률에 의해 권리와 의무의 주체 자격이 부여된 단체', 'CORP');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('보증', 'Guarantee', '채무 이행을 담보하는 행위', 'GRNT');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('부서', 'Department', '조직 내 특정 업무를 담당하는 단위', 'DEPT');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('비과세', 'Tax-Free', '이자나 소득에 대해 세금을 부과하지 않는 것', 'TXFR');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('상환', 'Repayment', '빌린 돈을 갚는 행위', 'REPY');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('상태', 'Status', '사물이나 시스템이 놓여있는 현재의 조건이나 상황', 'STAT');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('상품', 'Product', '판매를 목적으로 생산되거나 제공되는 유무형의 재화', 'PROD');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('서비스', 'Service', '고객 만족을 위해 제공하는 무형의 활동', 'SVC');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('송금', 'Remittance', '돈을 특정 수취인에게 보내는 행위', 'REMI');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('수익', 'Profit', '영업 활동을 통해 얻은 긍정적인 금전적 결과', 'PRFT');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('수수료', 'Fee', '서비스 제공의 대가로 받는 돈', 'FEE');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('승인', 'Approval', '요청된 거래나 행위를 허가하는 것', 'APPR');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('시스템', 'System', '업무 처리를 위한 정보 기술 구성 요소의 집합', 'SYS');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('시장', 'Market', '금융 자산이 거래되는 추상적 또는 물리적 공간', 'MKT');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('신규', 'New', '계약이나 관계를 처음 시작하는 것', 'NEW');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('신용', 'Credit', '미래의 상환을 약속하고 자금을 빌릴 수 있는 능력', 'CRD');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('신탁', 'Trust', '재산을 타인에게 맡겨 관리, 운용하게 하는 법률 관계', 'TRST');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('여신', 'Credit Line', '신용을 공여하는 행위 또는 그 한도', 'CLIN');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('연체', 'Overdue', '정해진 기일에 채무를 이행하지 못하고 지체하는 상태', 'OVD');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('예금', 'Deposit', '은행에 돈을 맡기는 행위 또는 그 돈', 'DEPO');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('외환', 'Foreign Exchange', '서로 다른 국가의 통화를 교환하는 거래', 'FX');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('원금', 'Principal', '이자를 발생시키는 최초의 자금', 'PRIN');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('유형', 'Type', '공통된 특성에 따라 분류한 갈래', 'TYPE');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('이자', 'Interest', '원금에 대해 약정된 이율에 따라 발생하는 금액', 'INT');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('이체', 'Transfer', '한 계좌에서 다른 계좌로 자금을 옮기는 거래', 'TRSF');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('인증', 'Authentication', '사용자가 본인임을 증명하는 절차', 'AUTH');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('입금', 'Credit Deposit', '계좌의 잔액을 늘리는 거래', 'CDEP');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('잔액', 'Balance', '특정 시점의 계좌에 남아있는 금액', 'BAL');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('채권', 'Bond', '자금 조달을 위해 발행하는 유가증권', 'BOND');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('채널', 'Channel', '고객이 서비스를 이용하는 경로', 'CHNL');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('청구', 'Billing', '사용 대금을 납부하도록 요청하는 행위', 'BILL');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('출금', 'Withdrawal', '계좌의 잔액을 줄이는 거래', 'WDRW');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('카드', 'Card', '지급결제 수단으로 사용되는 플라스틱 또는 모바일 형태의 증표', 'CARD');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('코드', 'Code', '정보를 식별하고 분류하기 위해 부여한 기호', 'CODE');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('통장', 'Passbook', '계좌의 거래 내역을 기록하는 실물 장부', 'PBOK');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('펀드', 'Fund', '다수의 투자자로부터 모은 자금을 운용하는 상품', 'FUND');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('할부', 'Installment', '대금을 여러 번에 걸쳐 나누어 내는 방식', 'INST');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('해지', 'Termination', '유효한 계약을 종료시키는 행위', 'TERM');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('확인', 'Verification', '어떤 사실이나 내용이 맞는지 검토하여 인정함', 'VERI');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('환율', 'Exchange Rate', '서로 다른 통화의 교환 비율', 'EXRT');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('개인', 'Individual', '자연인으로서의 한 사람', 'INDV');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('거래', 'Transaction', '자산, 부채, 자본의 증감 변화를 일으키는 사건', 'TRAN');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('결제', 'Payment', '거래 대금을 주고받아 거래 관계를 끝맺는 행위', 'PAY');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('기관', 'Institution', '특정 목적을 위해 설립된 조직이나 단체', 'INST');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('비용', 'Cost', '재화나 서비스를 얻기 위해 지출된 금전적 가치', 'COST');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('손익', 'Profit and Loss', '수익과 비용의 차액으로 계산되는 이익 또는 손실', 'PL');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('유동성', 'Liquidity', '자산을 현금으로 전환할 수 있는 용이성', 'LQD');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('직원', 'Employee', '기관에 고용되어 근무하는 사람', 'EMP');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('지급', 'Disbursement', '정해진 몫의 돈을 내어주는 행위', 'DISB');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('주식', 'Stock', '주식회사의 자본을 구성하는 단위', 'STCK');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('중도', 'Midway', '정해진 기간이나 과정의 중간', 'MID');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('현금', 'Cash', '지폐나 동전과 같이 실체가 있는 화폐', 'CASH');
INSERT INTO STND_WORD (WORD_NM, WORD_ENG_NM, WORD_DESC, WORD_ENG_ABR_NM) VALUES ('리스크', 'Risk', '잠재적 손실의 가능성', 'RISK');
