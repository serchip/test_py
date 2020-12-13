"""
test_utils.py
====================================
Тесты для папки app/utils/
"""

from app.utils.pgsql import generate_order_by, PGsqlOrderByExcept


class TestUtilsPgsql:
    """тесты для pgsql.py"""
    def test_generate_order_by(self):
        """генерация ORDER BY"""
        assert generate_order_by([], []) == ''
        assert generate_order_by(['id'], ['asc']) == "ORDER BY id ASC"
        assert generate_order_by(['id', 'name'], ['asc', 'desc']) == "ORDER BY id ASC, name DESC"
        try:
            generate_order_by(['id'], ['wrong_value'])
        except PGsqlOrderByExcept as e:
            assert 'sort_order value should consist of ASC or DESC but he wrong_value'