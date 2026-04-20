from app.pipeline.upload.zip_utils import group_zip_files, should_skip_zip_entry


def test_should_skip_zip_entry_filters_macos_zip_metadata_and_non_source_files():
    assert should_skip_zip_entry("__MACOSX/Python416/._classTest.py") is True
    assert should_skip_zip_entry("Python416/._classTest.py") is True
    assert should_skip_zip_entry("Python416/.DS_Store") is True
    assert should_skip_zip_entry("Python416/notes.txt") is True
    assert should_skip_zip_entry("Python416/classTest.py") is False
    assert should_skip_zip_entry("Java415/src/Main.java") is False
    assert should_skip_zip_entry("C415/src/main.c") is False
    assert should_skip_zip_entry("Cpp415/src/main.cpp") is False
    assert should_skip_zip_entry("Js415/src/app.js") is False


def test_group_zip_files_only_keeps_supported_source_entries():
    groups = group_zip_files(
        [
            "__MACOSX/Python416/._classTest.py",
            "Python416/._classTest.py",
            "Python416/classTest.py",
            "Python416/InclassWork5_rectangle.py",
            "C415/main.c",
            "Cpp415/main.cpp",
            "Js415/app.js",
            "Python416/.DS_Store",
            "Python416/readme.txt",
        ]
    )

    assert groups == {
        "Python416": [
            "Python416/classTest.py",
            "Python416/InclassWork5_rectangle.py",
        ],
        "C415": ["C415/main.c"],
        "Cpp415": ["Cpp415/main.cpp"],
        "Js415": ["Js415/app.js"],
    }
