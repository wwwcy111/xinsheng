-- =============================================================
-- 【码道】新声——大一新生“破冰·学业·生活”全能赋能平台
-- MySQL 8.0 建表脚本
-- 引擎：InnoDB  字符集：utf8mb4  排序规则：utf8mb4_general_ci
-- 关联方式：逻辑外键 + 索引（不建物理 FOREIGN KEY，便于演示数据重置）
-- =============================================================

CREATE DATABASE IF NOT EXISTS `xinsheng`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE `xinsheng`;
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- -------------------------------------------------------------
-- 1. 用户信息表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `t_user`;
CREATE TABLE `t_user` (
  `id`                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID，主键',
  `nickname`          VARCHAR(20)     NOT NULL                COMMENT '昵称，1-20字，平台内唯一',
  `student_no_tail4`  CHAR(4)         NOT NULL                COMMENT '学号后四位，轻量身份标识',
  `password_hash`     VARCHAR(100)    NOT NULL                COMMENT '口令哈希（bcrypt），禁止明文存储',
  `avatar_url`        VARCHAR(500)    DEFAULT NULL            COMMENT '头像地址',
  `college`           VARCHAR(50)     DEFAULT NULL            COMMENT '学院，可为空，用于同院系优先推荐',
  `major`             VARCHAR(50)     DEFAULT NULL            COMMENT '专业，可为空',
  `class_name`        VARCHAR(50)     DEFAULT NULL            COMMENT '班级，可为空',
  `personality`       VARCHAR(10)     NOT NULL DEFAULT 'neutral' COMMENT '性格倾向：introvert内向/neutral中性/extrovert外向',
  `social_pref`       VARCHAR(20)     NOT NULL DEFAULT 'random'  COMMENT '社交偏好：one_to_one一对一深聊/small_group小群体/random随缘',
  `contact`           VARCHAR(50)     DEFAULT NULL            COMMENT '联系方式（微信/QQ/手机），仅按关系展示',
  `bio`               VARCHAR(200)    DEFAULT NULL            COMMENT '个人简介',
  `status`            TINYINT UNSIGNED NOT NULL DEFAULT 1     COMMENT '账号状态：1正常 0封禁',
  `login_fail_count`  TINYINT UNSIGNED NOT NULL DEFAULT 0     COMMENT '连续登录失败次数，达5次锁定',
  `lock_until`        DATETIME        DEFAULT NULL            COMMENT '账号锁定截止时间',
  `last_login_at`     DATETIME        DEFAULT NULL            COMMENT '最近登录时间',
  `created_at`        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
  `updated_at`        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_nickname` (`nickname`),
  KEY `idx_status` (`status`),
  KEY `idx_college` (`college`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='用户信息表';

-- -------------------------------------------------------------
-- 2. 兴趣标签表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `t_tag`;
CREATE TABLE `t_tag` (
  `id`         INT UNSIGNED    NOT NULL AUTO_INCREMENT COMMENT '标签ID',
  `tag_name`   VARCHAR(20)     NOT NULL                COMMENT '标签名称，如“篮球”“编程”“摄影”',
  `category`   VARCHAR(20)     NOT NULL                COMMENT '标签分类：sports运动/arts艺术/game游戏/study学习/life生活/food美食/travel旅行',
  `icon`       VARCHAR(50)     DEFAULT NULL            COMMENT '标签图标（emoji 或图标名）',
  `sort_no`    INT             NOT NULL DEFAULT 0      COMMENT '展示排序号，越小越靠前',
  `status`     TINYINT UNSIGNED NOT NULL DEFAULT 1     COMMENT '状态：1启用 0停用',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tag_name` (`tag_name`),
  KEY `idx_category_sort` (`category`, `sort_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='兴趣标签表';

-- -------------------------------------------------------------
-- 3. 用户-兴趣标签关联表（多对多，单用户 3-10 个标签）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `t_user_tag`;
CREATE TABLE `t_user_tag` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id`    BIGINT UNSIGNED NOT NULL                COMMENT '用户ID，关联 t_user.id',
  `tag_id`     INT UNSIGNED    NOT NULL                COMMENT '标签ID，关联 t_tag.id',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '选择时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_tag` (`user_id`, `tag_id`),
  KEY `idx_tag_id` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='用户兴趣标签关联表';

-- -------------------------------------------------------------
-- 4. 搭子匹配记录表（每日推荐批次）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `t_match_record`;
CREATE TABLE `t_match_record` (
  `id`              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '匹配记录ID',
  `user_id`         BIGINT UNSIGNED NOT NULL                COMMENT '推荐接收方用户ID',
  `target_user_id`  BIGINT UNSIGNED NOT NULL                COMMENT '被推荐搭子用户ID',
  `score`           TINYINT UNSIGNED NOT NULL DEFAULT 0     COMMENT '匹配度分值，0-100整数',
  `common_tag_ids`  JSON            DEFAULT NULL            COMMENT '共同兴趣标签ID数组，如 [1,5,9]',
  `match_reason`    VARCHAR(200)    DEFAULT NULL            COMMENT '匹配理由，至少包含1个共同标签',
  `batch_date`      DATE            NOT NULL                COMMENT '推荐批次日期，每日一批',
  `status`          VARCHAR(20)     NOT NULL DEFAULT 'recommended' COMMENT '状态：recommended已推荐/greeted已招呼/matched已互选/ignored已忽略',
  `created_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_target_date` (`user_id`, `target_user_id`, `batch_date`),
  KEY `idx_user_batch` (`user_id`, `batch_date`),
  KEY `idx_target_user` (`target_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='搭子匹配记录表';

-- -------------------------------------------------------------
-- 5. 破冰话题表（匹配记录从表，每条匹配生成3条）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `t_icebreaker_topic`;
CREATE TABLE `t_icebreaker_topic` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '话题ID',
  `match_id`   BIGINT UNSIGNED NOT NULL                COMMENT '关联匹配记录ID，t_match_record.id',
  `content`    VARCHAR(100)    NOT NULL                COMMENT '破冰话题文本，15-60字，可直接复制发送',
  `used_flag`  TINYINT UNSIGNED NOT NULL DEFAULT 0     COMMENT '是否已使用：1已复制或已发送 0未使用',
  `sort_no`    TINYINT UNSIGNED NOT NULL DEFAULT 0     COMMENT '展示顺序',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
  PRIMARY KEY (`id`),
  KEY `idx_match_id` (`match_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='破冰话题表';

-- -------------------------------------------------------------
-- 6. 笔记上传记录表（含 AI 三类产出）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `t_study_note`;
CREATE TABLE `t_study_note` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '笔记ID',
  `owner_id`      BIGINT UNSIGNED NOT NULL                COMMENT '上传者用户ID，关联 t_user.id',
  `file_name`     VARCHAR(255)    NOT NULL                COMMENT '原始文件名',
  `file_url`      VARCHAR(500)    NOT NULL                COMMENT '文件访问地址（本地 uploads 或 OBS）',
  `file_type`     VARCHAR(10)     NOT NULL                COMMENT '文件类型：jpg/png/webp/pdf',
  `file_size`     INT UNSIGNED    NOT NULL                COMMENT '文件大小，单位字节，上限20MB',
  `ocr_text`      LONGTEXT        DEFAULT NULL            COMMENT 'OCR识别原始文本',
  `char_count`    INT UNSIGNED    NOT NULL DEFAULT 0      COMMENT 'OCR有效字符数，小于20判定识别失败',
  `mind_map`      JSON            DEFAULT NULL            COMMENT '思维导图结构 {"title":"","children":[]}，层级≥2、节点≥8',
  `summaries`     JSON            DEFAULT NULL            COMMENT '知识点摘要数组 ["..."], 5-10条，单条≤80字',
  `exercises`     JSON            DEFAULT NULL            COMMENT '复习练习题数组 [{"question":"","answer":"","analysis":""}]，≥5道',
  `status`        VARCHAR(20)     NOT NULL DEFAULT 'ocr_pending' COMMENT '处理状态：ocr_pending识别中/generating生成中/completed完成/failed失败',
  `retry_count`   TINYINT UNSIGNED NOT NULL DEFAULT 0     COMMENT '生成失败重试次数，上限3次',
  `error_message` VARCHAR(255)    DEFAULT NULL            COMMENT '失败原因，用于前端提示',
  `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  `updated_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_owner_created` (`owner_id`, `created_at`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='笔记上传记录表';

-- -------------------------------------------------------------
-- 7. 二手物品表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `t_secondhand_item`;
CREATE TABLE `t_secondhand_item` (
  `id`               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '商品ID',
  `seller_id`        BIGINT UNSIGNED NOT NULL                COMMENT '卖家用户ID，关联 t_user.id',
  `title`            VARCHAR(50)     NOT NULL                COMMENT '商品标题',
  `description`      VARCHAR(500)    DEFAULT NULL            COMMENT '商品描述（新旧程度、使用情况等）',
  `price`            DECIMAL(10,2)   NOT NULL                COMMENT '售价，0-9999元',
  `original_price`   DECIMAL(10,2)   DEFAULT NULL            COMMENT '购入原价，仅作参考',
  `condition_level`  VARCHAR(10)     NOT NULL                COMMENT '成色：new全新/nine九成新/seven七成新/usable可用',
  `category`         VARCHAR(20)     NOT NULL DEFAULT 'other' COMMENT '分类：textbook教材/digital数码/life生活/sports运动/other其他',
  `trade_place`      VARCHAR(100)    NOT NULL                COMMENT '线下交易地点，如“一食堂门口”',
  `image_urls`       JSON            DEFAULT NULL            COMMENT '商品图片地址数组，1-6张',
  `status`           VARCHAR(20)     NOT NULL DEFAULT 'on_sale' COMMENT '状态：on_sale在售/intended有意向/sold已售/off_shelf已下架',
  `view_count`       INT UNSIGNED    NOT NULL DEFAULT 0      COMMENT '浏览量',
  `created_at`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
  `updated_at`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_status_created` (`status`, `created_at`),
  KEY `idx_seller` (`seller_id`),
  KEY `idx_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='二手物品表';

-- -------------------------------------------------------------
-- 8. 失物招领表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `t_lost_found`;
CREATE TABLE `t_lost_found` (
  `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '失物招领ID',
  `publisher_id` BIGINT UNSIGNED NOT NULL                COMMENT '发布者用户ID，关联 t_user.id',
  `type`         VARCHAR(10)     NOT NULL                COMMENT '类型：lost失物/found招领',
  `title`        VARCHAR(50)     NOT NULL                COMMENT '标题，如“丢失一张校园卡”',
  `item_desc`    VARCHAR(500)    NOT NULL                COMMENT '物品描述（名称、颜色、特征）',
  `category`     VARCHAR(20)     NOT NULL DEFAULT 'other' COMMENT '分类：card证件/electronic电子/keys钥匙/book书籍/other其他',
  `event_time`   DATETIME        DEFAULT NULL            COMMENT '丢失或拾获时间',
  `event_place`  VARCHAR(100)    NOT NULL                COMMENT '丢失或拾获地点',
  `contact`      VARCHAR(50)     NOT NULL                COMMENT '联系说明（微信/电话/领取方式）',
  `images`       JSON            DEFAULT NULL            COMMENT '物品图片地址数组',
  `status`       VARCHAR(20)     NOT NULL DEFAULT 'ongoing' COMMENT '状态：ongoing进行中/returned已归还/closed已关闭',
  `claim_count`  INT UNSIGNED    NOT NULL DEFAULT 0      COMMENT '认领申请数量',
  `created_at`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
  `updated_at`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_type_status` (`type`, `status`),
  KEY `idx_publisher` (`publisher_id`),
  KEY `idx_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='失物招领表';

-- -------------------------------------------------------------
-- 9. 活动信息表（讲座、社团招新、校内活动）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `t_activity`;
CREATE TABLE `t_activity` (
  `id`              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '活动ID',
  `title`           VARCHAR(100)    NOT NULL                COMMENT '活动标题',
  `type`            VARCHAR(20)     NOT NULL DEFAULT 'other' COMMENT '类型：lecture讲座/club_recruit社团招新/sports文体/other其他',
  `host`            VARCHAR(100)    NOT NULL                COMMENT '主办方或社团名称',
  `cover_url`       VARCHAR(500)    DEFAULT NULL            COMMENT '活动封面图地址',
  `description`     TEXT            DEFAULT NULL            COMMENT '活动详情',
  `start_time`      DATETIME        NOT NULL                COMMENT '开始时间',
  `end_time`        DATETIME        NOT NULL                COMMENT '结束时间',
  `place`           VARCHAR(100)    NOT NULL                COMMENT '活动地点',
  `quota`           INT UNSIGNED    NOT NULL                COMMENT '名额总数',
  `remaining`       INT UNSIGNED    NOT NULL                COMMENT '剩余名额，0表示已满',
  `signup_deadline` DATETIME        DEFAULT NULL            COMMENT '报名截止时间',
  `status`          VARCHAR(20)     NOT NULL DEFAULT 'signing' COMMENT '状态：signing报名中/ended已结束/cancelled已取消',
  `created_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_start_time` (`start_time`),
  KEY `idx_status` (`status`),
  KEY `idx_type` (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='活动信息表';

-- -------------------------------------------------------------
-- 10. 学习搭子招募帖表（学霸互助圈业务闭环）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `t_study_post`;
CREATE TABLE `t_study_post` (
  `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '招募帖ID',
  `author_id`    BIGINT UNSIGNED NOT NULL                COMMENT '发布者用户ID，关联 t_user.id',
  `title`        VARCHAR(50)     NOT NULL                COMMENT '招募标题，如“期末高数复习搭子”',
  `type`         VARCHAR(20)     NOT NULL                COMMENT '类型：evening_study晚自习/final_review期末复习/other其他',
  `description`  VARCHAR(500)    DEFAULT NULL            COMMENT '补充说明（复习科目、目标等）',
  `start_time`   DATETIME        NOT NULL                COMMENT '约定开始时间',
  `location`     VARCHAR(100)    NOT NULL                COMMENT '自习或复习地点，如“图书馆三楼”',
  `capacity`     TINYINT UNSIGNED NOT NULL               COMMENT '人数上限，至少2人',
  `joined_count` TINYINT UNSIGNED NOT NULL DEFAULT 0     COMMENT '已报名人数，不得超过人数上限',
  `status`       VARCHAR(20)     NOT NULL DEFAULT 'pending' COMMENT '状态：pending待审核/published已发布/full已满/offline已下架',
  `created_at`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
  `updated_at`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_status_created` (`status`, `created_at`),
  KEY `idx_author` (`author_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='学习搭子招募帖表';

-- -------------------------------------------------------------
-- 11. 招募报名表（唯一键保证不重复报名）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `t_study_signup`;
CREATE TABLE `t_study_signup` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '报名ID',
  `post_id`    BIGINT UNSIGNED NOT NULL                COMMENT '招募帖ID，关联 t_study_post.id',
  `user_id`    BIGINT UNSIGNED NOT NULL                COMMENT '报名用户ID，关联 t_user.id',
  `status`     VARCHAR(20)     NOT NULL DEFAULT 'signed' COMMENT '状态：signed已报名/cancelled已取消',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '报名时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_post_user` (`post_id`, `user_id`),
  KEY `idx_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='学习搭子招募报名表';

-- -------------------------------------------------------------
-- 12. 活动报名表（唯一键保证不重复报名）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `t_activity_signup`;
CREATE TABLE `t_activity_signup` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '报名ID',
  `activity_id` BIGINT UNSIGNED NOT NULL                COMMENT '活动ID，关联 t_activity.id',
  `user_id`     BIGINT UNSIGNED NOT NULL                COMMENT '报名用户ID，关联 t_user.id',
  `status`      VARCHAR(20)     NOT NULL DEFAULT 'signed' COMMENT '状态：signed已报名/cancelled已取消',
  `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '报名时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_activity_user` (`activity_id`, `user_id`),
  KEY `idx_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='活动报名表';

SET FOREIGN_KEY_CHECKS = 1;