-- This migration drops ybgin indexes due to existing limitation to use it with other indexes.
-- https://docs.yugabyte.com/preview/explore/ysql-language-features/indexes-constraints/gin/#limitations.
DROP INDEX s_cell_idx;
DROP INDEX isa_cell_idx;
