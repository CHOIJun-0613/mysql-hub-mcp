-- MySQL dump 10.13  Distrib 8.0.33, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: devdb
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `STND_WORD`
--

DROP TABLE IF EXISTS `STND_WORD`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `STND_WORD` (
  `WORD_NM` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '단어명 (한글)',
  `WORD_ENG_NM` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '단어 영문명',
  `WORD_DESC` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '단어 설명',
  `WORD_ENG_ABR_NM` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '단어 영문 약어명',
  PRIMARY KEY (`WORD_NM`) COMMENT '단어명 기본키'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='표준 단어';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `STND_WORD`
--

/*!40000 ALTER TABLE `STND_WORD` DISABLE KEYS */;
INSERT INTO `STND_WORD` VALUES ('개인','Individual','자연인으로서의 한 사람','INDV'),('거래','Transaction','자산, 부채, 자본의 증감 변화를 일으키는 사건','TRAN'),('결제','Payment','거래 대금을 주고받아 거래 관계를 끝맺는 행위','PAY'),('계좌','Account','금융 거래를 기록하고 관리하기 위한 기본 단위','ACCT'),('고객','Customer','은행과 금융 거래를 하는 개인 또는 법인 주체','CUST'),('금리','Interest Rate','원금에 대해 부과되는 이자율','IRT'),('금액','Amount','화폐 단위로 표시된 값','AMT'),('기간','Period','정해진 시간의 길이. 시작과 끝이 있는 시간의 간격','PRD'),('기관','Institution','특정 목적을 위해 설립된 조직이나 단체','INST'),('담보','Collateral','채무 변제를 보증하기 위해 제공하는 자산','COL'),('대출','Loan','은행이 고객에게 자금을 빌려주는 금융 상품','LOAN'),('등급','Grade','일정한 기준에 따라 매겨진 서열이나 수준','GRD'),('리스크','Risk','잠재적 손실의 가능성','RISK'),('마감','Closing','하루의 거래를 정산하여 회계 장부를 마치는 절차','CLS'),('만기','Maturity','계약이 종료되어 효력이 발생하는 시점','MTRT'),('매입','Purchase','대금을 지급하고 자산이나 권리를 사는 행위','PURC'),('번호','Number','대상을 식별하기 위해 부여하는 일련의 숫자나 기호','NO'),('법인','Corporation','법률에 의해 권리와 의무의 주체 자격이 부여된 단체','CORP'),('보증','Guarantee','채무 이행을 담보하는 행위','GRNT'),('부서','Department','조직 내 특정 업무를 담당하는 단위','DEPT'),('비과세','Tax-Free','이자나 소득에 대해 세금을 부과하지 않는 것','TXFR'),('비용','Cost','재화나 서비스를 얻기 위해 지출된 금전적 가치','COST'),('상태','Status','사물이나 시스템이 놓여있는 현재의 조건이나 상황','STAT'),('상품','Product','판매를 목적으로 생산되거나 제공되는 유무형의 재화','PROD'),('상환','Repayment','빌린 돈을 갚는 행위','REPY'),('서비스','Service','고객 만족을 위해 제공하는 무형의 활동','SVC'),('손익','Profit and Loss','수익과 비용의 차액으로 계산되는 이익 또는 손실','PL'),('송금','Remittance','돈을 특정 수취인에게 보내는 행위','REMI'),('수수료','Fee','서비스 제공의 대가로 받는 돈','FEE'),('수익','Profit','영업 활동을 통해 얻은 긍정적인 금전적 결과','PRFT'),('승인','Approval','요청된 거래나 행위를 허가하는 것','APPR'),('시스템','System','업무 처리를 위한 정보 기술 구성 요소의 집합','SYS'),('시장','Market','금융 자산이 거래되는 추상적 또는 물리적 공간','MKT'),('신규','New','계약이나 관계를 처음 시작하는 것','NEW'),('신용','Credit','미래의 상환을 약속하고 자금을 빌릴 수 있는 능력','CRD'),('신탁','Trust','재산을 타인에게 맡겨 관리, 운용하게 하는 법률 관계','TRST'),('여신','Credit Line','신용을 공여하는 행위 또는 그 한도','CLIN'),('연체','Overdue','정해진 기일에 채무를 이행하지 못하고 지체하는 상태','OVD'),('예금','Deposit','은행에 돈을 맡기는 행위 또는 그 돈','DEPO'),('외환','Foreign Exchange','서로 다른 국가의 통화를 교환하는 거래','FX'),('원금','Principal','이자를 발생시키는 최초의 자금','PRIN'),('유동성','Liquidity','자산을 현금으로 전환할 수 있는 용이성','LQD'),('유형','Type','공통된 특성에 따라 분류한 갈래','TYPE'),('이자','Interest','원금에 대해 약정된 이율에 따라 발생하는 금액','INT'),('이체','Transfer','한 계좌에서 다른 계좌로 자금을 옮기는 거래','TRSF'),('인증','Authentication','사용자가 본인임을 증명하는 절차','AUTH'),('입금','Credit Deposit','계좌의 잔액을 늘리는 거래','CDEP'),('잔액','Balance','특정 시점의 계좌에 남아있는 금액','BAL'),('주식','Stock','주식회사의 자본을 구성하는 단위','STCK'),('중도','Midway','정해진 기간이나 과정의 중간','MID'),('지급','Disbursement','정해진 몫의 돈을 내어주는 행위','DISB'),('직원','Employee','기관에 고용되어 근무하는 사람','EMP'),('채권','Bond','자금 조달을 위해 발행하는 유가증권','BOND'),('채널','Channel','고객이 서비스를 이용하는 경로','CHNL'),('청구','Billing','사용 대금을 납부하도록 요청하는 행위','BILL'),('출금','Withdrawal','계좌의 잔액을 줄이는 거래','WDRW'),('카드','Card','지급결제 수단으로 사용되는 플라스틱 또는 모바일 형태의 증표','CARD'),('코드','Code','정보를 식별하고 분류하기 위해 부여한 기호','CODE'),('통장','Passbook','계좌의 거래 내역을 기록하는 실물 장부','PBOK'),('펀드','Fund','다수의 투자자로부터 모은 자금을 운용하는 상품','FUND'),('할부','Installment','대금을 여러 번에 걸쳐 나누어 내는 방식','INST'),('해지','Termination','유효한 계약을 종료시키는 행위','TERM'),('현금','Cash','지폐나 동전과 같이 실체가 있는 화폐','CASH'),('확인','Verification','어떤 사실이나 내용이 맞는지 검토하여 인정함','VERI'),('환율','Exchange Rate','서로 다른 통화의 교환 비율','EXRT');
/*!40000 ALTER TABLE `STND_WORD` ENABLE KEYS */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-08-24 14:20:39
