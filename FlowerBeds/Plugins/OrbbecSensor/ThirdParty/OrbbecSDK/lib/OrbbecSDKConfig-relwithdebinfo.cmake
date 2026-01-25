#----------------------------------------------------------------
# Generated CMake target import file for configuration "RelWithDebInfo".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "ob::OrbbecSDK" for configuration "RelWithDebInfo"
set_property(TARGET ob::OrbbecSDK APPEND PROPERTY IMPORTED_CONFIGURATIONS RELWITHDEBINFO)
set_target_properties(ob::OrbbecSDK PROPERTIES
  IMPORTED_IMPLIB_RELWITHDEBINFO "${_IMPORT_PREFIX}/lib/OrbbecSDK.lib"
  IMPORTED_LOCATION_RELWITHDEBINFO "${_IMPORT_PREFIX}/bin/OrbbecSDK.dll"
  )

list(APPEND _cmake_import_check_targets ob::OrbbecSDK )
list(APPEND _cmake_import_check_files_for_ob::OrbbecSDK "${_IMPORT_PREFIX}/lib/OrbbecSDK.lib" "${_IMPORT_PREFIX}/bin/OrbbecSDK.dll" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
