-- MySQL dump 10.13  Distrib 8.0.36, for Win64 (x86_64)
--
-- Host: localhost    Database: placehistory
-- ------------------------------------------------------
-- Server version	8.0.36

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
-- Table structure for table `admin_notifications`
--

DROP TABLE IF EXISTS `admin_notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin_notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `recipient_type` enum('student','tpo','all') NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin_notifications`
--

LOCK TABLES `admin_notifications` WRITE;
/*!40000 ALTER TABLE `admin_notifications` DISABLE KEYS */;
INSERT INTO `admin_notifications` VALUES (1,'Website issue','Website will be down','all','2025-02-28 21:18:55'),(2,'Website will be closed','Website will be closed tomorrow ','all','2025-03-05 19:35:15'),(3,'Website will be closed','Website will be closed tomorrow ','all','2025-03-05 19:37:50'),(4,'Website Issue','Website will be under maintenance till 9th March 2025 ','all','2025-03-07 05:48:42'),(5,'Website issue','Website will be closed for today','all','2025-04-17 08:18:17'),(6,'Website announcement','Website will be closed for maintenance','all','2025-04-21 05:55:57');
/*!40000 ALTER TABLE `admin_notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `companies`
--

DROP TABLE IF EXISTS `companies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `companies` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_name` varchar(100) DEFAULT NULL,
  `job_role` varchar(100) DEFAULT NULL,
  `description` text,
  `apply_link` varchar(255) DEFAULT NULL,
  `apply_deadline` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `companies`
--

LOCK TABLES `companies` WRITE;
/*!40000 ALTER TABLE `companies` DISABLE KEYS */;
INSERT INTO `companies` VALUES (6,'Galaxy Office Automation Pvt. Ltd. ','Junior Software Associate','  Qualifications  :-\r\n  Bachelor\'s/Master\'s degree in Computer Science, Information Technology, Engineering, orrelated fields.\r\n\r\nEligibility criterion-: Good communication skills (both oral and written), CGPA of 7+, no backs\r\n\r\nAverage:- CTC: 3.15 L p.a. + Gratuity + Mediclaim Insuranc\r\n\r\nLocation:- Mumbai, Pune or Bangalore\r\n\r\nSelection Process: -Aptitude assessment test, Communication skills assessment test, Technical Interview, HR Interview\r\n  ','https://forms.gle/Wz89ZTw1gx1QAchw9','2025-04-28');
/*!40000 ALTER TABLE `companies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_id` int DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `recipient_type` enum('student','tpo','all') NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `scheduled_on` datetime DEFAULT NULL,
  `google_form_link` varchar(255) DEFAULT NULL,
  `status` enum('pending','sent','failed') DEFAULT 'pending',
  `email_sent` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `company_id` (`company_id`),
  CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications`
--

LOCK TABLES `notifications` WRITE;
/*!40000 ALTER TABLE `notifications` DISABLE KEYS */;
INSERT INTO `notifications` VALUES (11,NULL,'Seminar regarding placement drive ','A seminar is schedule tomorrow regarding placement drive. It is compulsory for all students to attend it.','student','2025-04-20 18:02:40',NULL,NULL,'pending',0),(12,6,'Galaxy Office Automation Pvt. Ltd.  - Junior Software Associate','\n    Galaxy Office Automation Pvt. Ltd.  - Junior Software Associate \n\n    Job Role: Junior Software Associate\n    Description :   Qualifications  :-\r\n  Bachelor\'s/Master\'s degree in Computer Science, Information Technology, Engineering, orrelated fields.\r\n\r\nEligibility criterion-: Good communication skills (both oral and written), CGPA of 7+, no backs\r\n\r\nAverage:- CTC: 3.15 L p.a. + Gratuity + Mediclaim Insuranc\r\n\r\nLocation:- Mumbai, Pune or Bangalore\r\n\r\nSelection Process: -Aptitude assessment test, Communication skills assessment test, Technical Interview, HR Interview\r\n  \n    Apply Link: https://forms.gle/oUcivXvf7z648US77\n    Apply Deadline: 2025-04-28\n    ','student','2025-04-20 18:10:25',NULL,NULL,'pending',0),(13,6,'Galaxy Office Automation Pvt. Ltd.  - Junior Software Associate','\n    Galaxy Office Automation Pvt. Ltd.  - Junior Software Associate \n\n    Job Role: Junior Software Associate\n    Description :   Qualifications  :-\r\n  Bachelor\'s/Master\'s degree in Computer Science, Information Technology, Engineering, orrelated fields.\r\n\r\nEligibility criterion-: Good communication skills (both oral and written), CGPA of 7+, no backs\r\n\r\nAverage:- CTC: 3.15 L p.a. + Gratuity + Mediclaim Insuranc\r\n\r\nLocation:- Mumbai, Pune or Bangalore\r\n\r\nSelection Process: -Aptitude assessment test, Communication skills assessment test, Technical Interview, HR Interview\r\n  \n    Apply Link: https://forms.gle/Wz89ZTw1gx1QAchw9\n    Apply Deadline: 2025-04-28\n    ','student','2025-04-20 18:40:21',NULL,NULL,'pending',0),(14,NULL,'Website announcement','Website will be closed for maintenance','student','2025-04-21 05:55:57',NULL,NULL,'pending',0);
/*!40000 ALTER TABLE `notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `queries`
--

DROP TABLE IF EXISTS `queries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `queries` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` int DEFAULT NULL,
  `query_text` text,
  `submitted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(20) DEFAULT 'pending',
  `reply_text` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `queries`
--

LOCK TABLES `queries` WRITE;
/*!40000 ALTER TABLE `queries` DISABLE KEYS */;
INSERT INTO `queries` VALUES (9,17,'How to build a resume??','2025-04-20 18:03:31','replied','We will arrange a seminar regarding your concerns.'),(10,17,'How can I prepare for aptitude?','2025-04-21 07:22:27','replied','We will arrange a seminar regarding your concerns.');
/*!40000 ALTER TABLE `queries` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students`
--

DROP TABLE IF EXISTS `students`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `username` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `signup_date` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students`
--

LOCK TABLES `students` WRITE;
/*!40000 ALTER TABLE `students` DISABLE KEYS */;
INSERT INTO `students` VALUES (17,'Sakshi Pawar','Sakshi','sakshii970320@gmail.com','9324625969','scrypt:32768:8:1$zs342FC2OLrg1Pvv$ac7262d837cccc04751256c5273af29db4cb62a62a216dfcb5c4e6e6f1d39723107fba17d8ee1fc694254988ae1d9993ebc3a2221e99c5b22bd16fe9baaa83a5','2025-04-20 22:40:29');
/*!40000 ALTER TABLE `students` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tpo`
--

DROP TABLE IF EXISTS `tpo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tpo` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `username` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `phone` varchar(15) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tpo`
--

LOCK TABLES `tpo` WRITE;
/*!40000 ALTER TABLE `tpo` DISABLE KEYS */;
INSERT INTO `tpo` VALUES (2,'Manaswi','Manaswi','manaswi0310@gmail.com','scrypt:32768:8:1$UKAE7IKY3MYazU8m$48960015cc9abe803a418e64ab9bbde4582c2d996389bd6b72c722c40e1326a6066ab769ee1fdfa49747ddba8f2c333e902abae67ae92fcff309c9a805867f71','9324455769'),(3,'Sayalee','Sayalee','sayaleepawar76032@gmail.com','scrypt:32768:8:1$U6m3dSiGjFblCvBL$b7653baa6bb9b8a663e82d97329680c9fc4c9e97aa44d0c26ba6710c4b7a9cc28337a51fdfcfce1b34e3eeb7f632a69ad070e91ea8182219ad9c256967460497','9769779069');
/*!40000 ALTER TABLE `tpo` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-04-24 14:19:26
