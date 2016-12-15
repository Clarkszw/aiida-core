# -*- coding: utf-8 -*-
"""
Generic tests that need the be specific to sqlalchemy
"""
from aiida.backends.tests.generic import TestCode, TestComputer, TestDbExtras, TestGroups, TestWfBasic
from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
from aiida.orm.node import Node

#
# class TestComputerSqla(SqlAlchemyTests, TestComputer):
#     """
#     No characterization required
#     """
#     pass
#
#
# class TestCodeSqla(SqlAlchemyTests, TestCode):
#     """
#      No characterization required
#      """
#     pass
#
#
# class TestWfBasicSqla(SqlAlchemyTests, TestWfBasic):
#     """
#      No characterization required
#      """
#     pass


class TestGroupsSqla(SqlAlchemyTests, TestGroups):
    """
     Characterized functions
     """

    def test_query(self):
        """
        Test if queries are working
        """
        from aiida.orm.group import Group
        from aiida.common.exceptions import NotExistent, MultipleObjectsError

        from aiida.backends.sqlalchemy.models.user import DbUser
        from aiida.backends.utils import get_automatic_user

        g1 = Group(name='testquery1').store()
        g2 = Group(name='testquery2').store()

        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()

        g1.add_nodes([n1, n2])
        g2.add_nodes([n1, n3])

        newuser = DbUser(email='test@email.xx', password='')
        g3 = Group(name='testquery3', user=newuser).store()

        # I should find it
        g1copy = Group.get(uuid=g1.uuid)
        self.assertEquals(g1.pk, g1copy.pk)

        # Try queries
        res = Group.query(nodes=n4)
        self.assertEquals([_.pk for _ in res], [])

        res = Group.query(nodes=n1)
        self.assertEquals([_.pk for _ in res], [_.pk for _ in [g1, g2]])

        res = Group.query(nodes=n2)
        self.assertEquals([_.pk for _ in res], [_.pk for _ in [g1]])

        # I try to use 'get' with zero or multiple results
        with self.assertRaises(NotExistent):
            Group.get(nodes=n4)
        with self.assertRaises(MultipleObjectsError):
            Group.get(nodes=n1)

        self.assertEquals(Group.get(nodes=n2).pk, g1.pk)

        # Query by user
        res = Group.query(user=newuser)
        self.assertEquals(set(_.pk for _ in res), set(_.pk for _ in [g3]))

        # Same query, but using a string (the username=email) instead of
        # a DbUser object
        res = Group.query(user=newuser.email)
        self.assertEquals(set(_.pk for _ in res), set(_.pk for _ in [g3]))

        res = Group.query(user=get_automatic_user())

        for re in res:
            print re.pk
        print

        self.assertEquals(set(_.pk for _ in res), set(_.pk for _ in [g1, g2]))

        # Final cleanup
        g1.delete()
        g2.delete()
        newuser.delete()


class TestDbExtrasSqla(SqlAlchemyTests, TestDbExtras):
    """
     Characterized functions
     """
    def test_replacement_1(self):

        n1 = Node().store()
        n2 = Node().store()

        n1.set_extra("pippo", [1, 2, u'a'])

        print "###First set####"
        print "n1 extra", n1.get_extras()
        print "n2 extra", n2.get_extras()

        n1.set_extra("pippobis", [5, 6, u'c'])

        print "###Second set####"
        print "n1 extra", n1.get_extras()
        print "n2 extra", n2.get_extras()

        n2.set_extra("pippo2", [3, 4, u'b'])

        print "###Third set####"
        print "n1 extra", n1.get_extras()
        print "n2 extra", n2.get_extras()

        self.assertEqual(n1.get_extras(),{'pippo': [1, 2, u'a'], 'pippobis': [5, 6, u'c']})

        self.assertEquals(n2.get_extras(), {'pippo2': [3, 4, 'b']})

        new_attrs = {"newval1": "v", "newval2": [1, {"c": "d", "e": 2}]}

        n1.reset_extras(new_attrs)
        self.assertEquals(n1.get_extras(), new_attrs)
        self.assertEquals(n2.get_extras(), {'pippo2': [3, 4, 'b']})

        n1.del_extra('newval2')
        del new_attrs['newval2']
        self.assertEquals(n1.get_extras(), new_attrs)
        # Also check that other nodes were not damaged
        self.assertEquals(n2.get_extras(), {'pippo2': [3, 4, 'b']})