/*
Navicat MySQL Data Transfer

Source Server         : 192.168.5.54
Source Server Version : 50729
Source Host           : 192.168.5.54:3306
Source Database       : dbname

Target Server Type    : MYSQL
Target Server Version : 50729
File Encoding         : 65001

Date: 2020-03-30 15:42:22
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for scheduler
-- ----------------------------
DROP TABLE IF EXISTS `scheduler`;
CREATE TABLE `scheduler` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `script_name` varchar(255) NOT NULL COMMENT '脚本位置名称',
  `schedule_name` varchar(255) NOT NULL,
  `schedule_desc` varchar(255) NOT NULL,
  `create_time` datetime(6) NOT NULL,
  `is_lock` int(11) DEFAULT NULL,
  `priority` int(11) NOT NULL,
  `cron_second` varchar(20) DEFAULT NULL,
  `cron_minutes` varchar(20) NOT NULL,
  `cron_hour` varchar(20) NOT NULL,
  `cron_day_of_month` varchar(20) NOT NULL,
  `cron_day_of_week` varchar(20) NOT NULL,
  `cron_month` varchar(20) NOT NULL,
  `enabled` int(11) NOT NULL,
  `run_type` varchar(20) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of scheduler
-- ----------------------------
INSERT INTO `scheduler` VALUES ('1', 'scheduler_script.example:run', 'example', 'example', '2020-03-30 15:40:09.696468', '1', '999', '*/5', '*', '*', '*', '*', '*', '0', '1');
INSERT INTO `scheduler` VALUES ('2', 'scheduler_script.example_class:run', 'example', 'example', '2020-03-30 15:40:25.528145', '1', '999', '*/5', '*', '*', '*', '*', '*', '0', '1');
