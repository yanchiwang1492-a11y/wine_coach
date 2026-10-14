-- ============================================================
-- WineCoach MySQL 建表脚本
-- 数据库：wine_coach
-- 表：user / question_library / practice_session / practice_message
-- ============================================================

CREATE DATABASE IF NOT EXISTS wine_coach DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE wine_coach;

-- 用户表（user 为 MySQL 保留字，需加反引号）
CREATE TABLE IF NOT EXISTS `user` (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    user_name VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) DEFAULT NULL COMMENT '邮箱（选填，用于发送评估报告）',
    role_name VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '角色：user/admin',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 已建库的老表升级（如果 user 表已存在且缺字段，执行下面两句补字段）：
-- ALTER TABLE `user` ADD COLUMN email VARCHAR(100) DEFAULT NULL AFTER password_hash;
-- ALTER TABLE `user` ADD COLUMN role_name VARCHAR(20) NOT NULL DEFAULT 'user' AFTER email;

-- 题库表（5 维度：题型 × 销售阶段 × 客户画像 × 酒类知识 × 国家）
CREATE TABLE IF NOT EXISTS question_library (
    question_id INT PRIMARY KEY AUTO_INCREMENT,
    question_title VARCHAR(500) NOT NULL,
    answer TEXT,
    question_type VARCHAR(50) NOT NULL COMMENT '题型：知识/话术/情景应对/产品推荐',
    sales_stage VARCHAR(50) NOT NULL COMMENT '销售阶段：迎宾/需求挖掘/推荐/异议处理/成交/售后/不限',
    customer_type VARCHAR(50) NOT NULL COMMENT '客户画像：新手/送礼/宴请/收藏/团购/不限',
    product_category VARCHAR(50) NOT NULL COMMENT '酒类知识：产区/品种/年份/配餐/储存/不限',
    country VARCHAR(50) NOT NULL DEFAULT '不限' COMMENT '国家：法国/意大利/西班牙/德国/葡萄牙/美国/智利/阿根廷/澳大利亚/新西兰/南非/中国/奥地利/希腊/格鲁吉亚/匈牙利/罗马尼亚/摩尔多瓦/乌拉圭/巴西/不限'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 已建库的老表升级：新增国家维度字段
-- ALTER TABLE question_library ADD COLUMN country VARCHAR(50) NOT NULL DEFAULT '不限' COMMENT '国家：法国/.../巴西/不限' AFTER product_category;

-- 练习会话表
CREATE TABLE IF NOT EXISTS practice_session (
    session_id VARCHAR(64) PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) DEFAULT '新练习',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_session_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 练习消息表
CREATE TABLE IF NOT EXISTS practice_message (
    message_id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(64) NOT NULL,
    user_id INT NOT NULL,
    role VARCHAR(20) NOT NULL COMMENT 'user/assistant',
    content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_message_session (session_id),
    KEY idx_message_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
