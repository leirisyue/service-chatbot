** Update Data
/sync/{table_name}/update
{
  "data": {
    "id_sap": "123",
    "material_name": "Vật liệu mới 3455555",
    "material_subgroup":"chờ",
    "material_group":"vật liệu mới "
  }
}

** Insert Data
/sync/{table_name}/insert
{
  "data": [
    {
    "id_sap": "123",
    "material_name": "Vật liệu mới 100001000358",
    "material_subgroup":"chờ",
    "material_group":"vật liệu mới "
    },{
      "id_sap": "456",
      "material_name": "Vật liệu mới 100001000358",
      "material_subgroup":"chờ",
      "material_group":"vật liệu mới "
    }
  ]
}

** Update Data By Keys
/sync/{table_name}/update/keys
{
  "list_key": [{ "material_name":"Vật liệu mới 100001000358"}],
  "data": {
    "material_name": "Vật liệu mới AA",
    "material_subgroup":"chờ",
    "material_group":"vật liệu mới "
  }
}