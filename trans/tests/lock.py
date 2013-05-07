# -*- coding: utf-8 -*-
#
# Copyright © 2012 - 2013 Michal Čihař <michal@cihar.com>
#
# This file is part of Weblate <http://weblate.org/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Tests for locking.
"""

from trans.tests.views import ViewTestCase
from django.core.urlresolvers import reverse


class LockTest(ViewTestCase):
    def setUp(self):
        super(LockTest, self).setUp()

        # Need extra power
        self.user.is_superuser = True
        self.user.save()

    def test_subproject(self):
        response = self.client.get(
            reverse('lock_subproject', kwargs=self.kw_subproject)
        )
        self.assertRedirects(
            response,
            reverse('subproject', kwargs=self.kw_subproject)
        )
        self.assertTrue(self.get_translation().subproject.locked)

        response = self.client.get(
            reverse('unlock_subproject', kwargs=self.kw_subproject)
        )
        self.assertRedirects(
            response,
            reverse('subproject', kwargs=self.kw_subproject)
        )
        self.assertFalse(self.get_translation().subproject.locked)

    def test_project(self):
        response = self.client.get(
            reverse('lock_project', kwargs=self.kw_project)
        )
        self.assertRedirects(
            response,
            reverse('project', kwargs=self.kw_project)
        )
        self.assertTrue(self.get_translation().subproject.locked)

        response = self.client.get(
            reverse('unlock_project', kwargs=self.kw_project)
        )
        self.assertRedirects(
            response,
            reverse('project', kwargs=self.kw_project)
        )
        self.assertFalse(self.get_translation().subproject.locked)