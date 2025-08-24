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
-- Table structure for table `STND_TERM`
--

DROP TABLE IF EXISTS `STND_TERM`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `STND_TERM` (
  `TERM_NM` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '용어명 (한글)',
  `TERM_ENG_NM` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '용어 영문명',
  `TERM_DESC` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '용어 설명',
  `TERM_ENG_ABR_NM` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '용어 영문 약어명 (단어약어_단어약어)',
  PRIMARY KEY (`TERM_NM`) COMMENT '용어명 기본키'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='표준 용어';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `STND_TERM`
--

/*!40000 ALTER TABLE `STND_TERM` DISABLE KEYS */;
INSERT INTO `STND_TERM` VALUES ('가맹점번호','Merchant Number','카드 결제가 가능한 가맹점에 부여된 고유 번호','MRCH_NO'),('가산금리','Spread Rate','기준금리에 신용도 등을 반영하여 추가로 더하는 금리','SPRD_IRT'),('개인고객','Individual Customer','개인 자격으로 은행과 거래하는 고객','INDV_CUST'),('거래금액','Transaction Amount','거래 시 발생한 금전의 액수','TRAN_AMT'),('거래일자','Transaction Date','금융 거래가 발생한 실제 날짜','TRAN_DT'),('거치기간','Grace Period','대출 실행 후 이자만 납부하고 원금 상환은 유예하는 기간','GRAC_PRD'),('결제금액','Payment Amount','결제일에 납부해야 할 총 카드대금','PAY_AMT'),('결제일자','Payment Date','카드 사용 대금이 계좌에서 출금되는 날짜','PAY_DT'),('계좌번호','Account Number','특정 계좌를 식별하기 위한 고유 번호','ACCT_NO'),('계좌비밀번호','Account Password','계좌에 접근하기 위한 비밀번호','ACCT_PW'),('계좌상태','Account Status','계좌의 현재 상태(정상, 해지, 지급정지 등)','ACCT_STAT'),('계좌잔액','Account Balance','특정 시점의 계좌에 남아있는 금액','ACCT_BAL'),('고객등급','Customer Grade','고객의 거래 기여도, 신용도 등을 종합하여 산정한 등급','CUST_GRD'),('고객번호','Customer Number','고객을 식별하기 위해 은행이 부여하는 고유 번호','CUST_NO'),('고객상태','Customer Status','고객의 현재 상태(정상, 휴면, 거래중지 등)','CUST_STAT'),('고객정보','Customer Information','고객의 신원, 연락처, 거래 정보 등을 포함하는 데이터','CUST_INFO'),('고객확인','Customer Verification','금융실명법 및 AML 규정에 따라 고객의 신원을 확인하는 절차','CUST_VERI'),('기준금리','Base Rate','대출금리를 정할 때 기준이 되는 금리','BASE_IRT'),('담보대출','Collateral Loan','부동산, 동산 등의 자산을 담보로 하는 대출','COL_LOAN'),('대출계좌','Loan Account','대출 거래를 관리하는 계좌','LOAN_ACCT'),('대출금리','Loan Interest Rate','대출 원금에 대해 부과되는 이자율','LOAN_IRT'),('대출상품','Loan Product','은행에서 판매하는 특정 조건의 대출 패키지','LOAN_PROD'),('대출잔액','Loan Balance','상환해야 할 대출 원금이 남아있는 금액','LOAN_BAL'),('대출한도','Loan Limit','고객에게 대출해 줄 수 있는 최대 금액','LOAN_LIM'),('만기일자','Maturity Date','예금, 대출 등의 계약이 종료되는 날짜','MTRT_DT'),('매입전표','Sales Slip','카드 결제 후 발생하는 매출 기록','SALE_SLIP'),('법인고객','Corporate Customer','기업, 기관 등 법인 자격으로 은행과 거래하는 고객','CORP_CUST'),('보증금액','Guarantee Amount','보증인이 채무 이행을 책임지는 금액','GRNT_AMT'),('보통예금','Savings Deposit','입출금이 자유로운 요구불예금의 한 종류','SVGS_DEPO'),('비밀번호','Password','본인 확인을 위해 사용하는 문자, 숫자 등의 조합','PW'),('상환방식','Repayment Method','대출 원리금을 상환하는 방식(원리금균등, 원금균등 등)','REPY_MTHD'),('승인번호','Approval Number','카드 거래가 승인될 때 부여되는 고유 번호','APPR_NO'),('신규일자','New Date','계좌, 대출 등을 처음 개설하거나 실행한 날짜','NEW_DT'),('신용대출','Credit Loan','고객의 신용을 바탕으로 담보 없이 실행되는 대출','CRD_LOAN'),('신용등급','Credit Grade','개인 또는 기업의 신용도를 평가하여 매긴 등급','CRD_GRD'),('신용정보','Credit Information','대출, 카드 사용 등 개인의 금융 거래 이력 정보','CRD_INFO'),('신용카드','Credit Card','신용을 바탕으로 후불 결제하는 카드','CRD_CARD'),('실명번호','Real Name Number','주민등록번호 또는 사업자등록번호와 같이 법적으로 실명을 확인할 수 있는 번호','REAL_NM_NO'),('여신한도','Credit Limit','은행이 특정 고객에게 제공할 수 있는 신용공여의 최대 총액','CRD_LIM'),('연체원금','Overdue Principal','상환일이 지났으나 아직 상환되지 않은 원금','OVD_PRIN'),('연체이자','Overdue Interest','연체된 원리금에 대하여 부과되는 이자','OVD_INT'),('예금잔액','Deposit Balance','예금 계좌에 남아있는 금액','DEPO_BAL'),('원금금액','Principal Amount','이자를 발생시키는 최초의 예금액 또는 대출금','PRIN_AMT'),('이자금액','Interest Amount','원금에 대해 약정된 이율에 따라 발생한 금액','INT_AMT'),('입금계좌','Deposit Account','자금이 들어오는 계좌','CDEP_ACCT'),('정기예금','Time Deposit','일정 기간 돈을 예치하고 만기일에 원리금을 받는 거치식 예금','TIME_DEPO'),('정기적금','Installment Savings','계약 기간 동안 매월 일정 금액을 납입하여 목돈을 마련하는 적립식 예금','INST_SVGS'),('주택담보대출','House Mortgage Loan','주택을 담보로 제공하고 받는 대출','HOUS_MRT_LOAN'),('중도상환','Midway Repayment','대출 만기 이전에 원금의 일부 또는 전부를 갚는 것','MID_REPY'),('지급정지','Stop Payment','분실, 도난 등의 사유로 계좌의 출금 거래를 정지시키는 조치','PAY_STOP'),('청구금액','Billing Amount','카드사가 회원에게 납부를 요청한 금액','BILL_AMT'),('체크카드','Debit Card','연결된 계좌에서 즉시 출금되는 카드','DEB_CARD'),('출금계좌','Withdrawal Account','자금이 빠져나가는 계좌','WDRW_ACCT'),('카드번호','Card Number','카드를 식별하는 16자리의 고유 번호','CARD_NO'),('카드상태','Card Status','카드의 현재 상태(정상, 분실, 정지 등)','CARD_STAT'),('카드한도','Card Limit','신용카드로 사용할 수 있는 최대 금액','CARD_LIM'),('할부개월','Installment Months','할부 결제 시 대금을 나누어 내는 개월 수','INST_MON'),('해지일자','Termination Date','금융 계약을 종료한 날짜','TERM_DT'),('현금서비스','Cash Advance','신용카드를 이용해 단기로 현금을 빌리는 서비스','CASH_SVC'),('휴면계좌','Dormant Account','장기간 거래가 없어 거래가 정지된 계좌','DRMT_ACCT');
/*!40000 ALTER TABLE `STND_TERM` ENABLE KEYS */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-08-24 14:20:28
