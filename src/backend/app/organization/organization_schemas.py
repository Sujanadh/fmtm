# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#
from pydantic import BaseModel



class Organisation(BaseModel):
    """
    Represents an organization.

    Attributes:
        slug (str): The unique identifier (slug) for the organization.
        name (str): The name of the organization.
        description (str): The description of the organization.
        url (str): The URL of the organization's website.
    """
    # id: int
    slug: str
    name: str
    description: str
    url: str
    # type: int
