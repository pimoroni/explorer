set(Python_FIND_VIRTUALENV "FIRST")
set(Python_FIND_UNVERSIONED_NAMES "FIRST")
set(Python_FIND_STRATEGY "LOCATION")
find_package (Python COMPONENTS Interpreter Development)

message("dir2uf2/py_decl: Using Python ${Python_EXECUTABLE}")

get_filename_component(PIMORONI_ROMFS_DIR ${PIMORONI_ROMFS_DIR} REALPATH)
get_filename_component(PIMORONI_LFS_DIR ${PIMORONI_LFS_DIR} REALPATH)

if (EXISTS "${PIMORONI_TOOLS_DIR}/py_decl/py_decl.py")
    add_custom_target("${MICROPY_TARGET}-verify" ALL
        COMMAND ${Python_EXECUTABLE} "${PIMORONI_TOOLS_DIR}/py_decl/py_decl.py" --to-json --verify "${CMAKE_CURRENT_BINARY_DIR}/${MICROPY_TARGET}.uf2"
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "pydecl: Verifying ${MICROPY_TARGET}.uf2"
        DEPENDS ${MICROPY_TARGET}
    )
endif()

if (EXISTS "${MICROPY_DIR}/tools/mpremote/mpremote.py" AND EXISTS "${PIMORONI_ROMFS_DIR}")
    add_custom_target("${MICROPY_TARGET}-romfs.bin" ALL
        COMMAND ${Python_EXECUTABLE} "${MICROPY_DIR}/tools/mpremote/mpremote.py" romfs --output "${CMAKE_BINARY_DIR}/${MICROPY_TARGET}-romfs.bin" build "${PIMORONI_ROMFS_DIR}"
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "mpremote romfs build: Packing ROMFS filesystem to ${MICROPY_TARGET}-romfs.bin."
        DEPENDS ${MICROPY_TARGET}
        DEPENDS "${MICROPY_TARGET}-verify"
    )
endif()

if (EXISTS "${PIMORONI_TOOLS_DIR}/dir2uf2/dir2uf2" AND EXISTS "${PIMORONI_ROMFS_DIR}")
    add_custom_target("${MICROPY_TARGET}-romfs.uf2" ALL
        COMMAND ${Python_EXECUTABLE} "${PIMORONI_TOOLS_DIR}/dir2uf2/dir2uf2" --fs-blockdev ROMFS --sparse --append-to "${MICROPY_TARGET}.uf2" --filename romfs.uf2 "${CMAKE_BINARY_DIR}/${MICROPY_TARGET}-romfs.bin"
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "dir2uf2: Appending ROMFS to ${MICROPY_TARGET}.uf2."
        DEPENDS "${MICROPY_TARGET}-romfs.bin"
        DEPENDS "${MICROPY_TARGET}-verify"
    )
endif()

if (EXISTS "${PIMORONI_TOOLS_DIR}/dir2uf2/dir2uf2" AND EXISTS "${PIMORONI_LFS_DIR}")
    add_custom_target("${MICROPY_TARGET}-romfs-with-filesystem.uf2" ALL
        COMMAND ${Python_EXECUTABLE} "${PIMORONI_TOOLS_DIR}/dir2uf2/dir2uf2" --fs-compact --sparse --append-to "${MICROPY_TARGET}-romfs.uf2" --filename with-filesystem.uf2 "${PIMORONI_LFS_DIR}/"
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "dir2uf2: Appending LittleFS filesystem to ${MICROPY_TARGET}-romfs.uf2."
        DEPENDS "${MICROPY_TARGET}-romfs.uf2"
    )
endif()
