from car_fault_detection.data.inventory import inspect_dataset


def test_absent_data_is_reported_without_creating_directory(tmp_path):
    path = tmp_path / "data"
    result = inspect_dataset(path)
    assert result["audio_files"] == 0
    assert not path.exists()


def test_nested_split_labels_match_existing_training_layout(tmp_path):
    audio = tmp_path / "train/idle state/normal_engine_idle/test.WAV"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"fixture; not real engine audio")
    (audio.parent / "empty.wav").write_bytes(b"")
    (audio.parent / "link.wav").symlink_to(audio)
    result = inspect_dataset(tmp_path)
    assert result["audio_files"] == 1
    assert result["class_counts"] == {"normal_engine_idle": 1}
    assert result["split_counts"] == {"train": 1}
    assert len(result["empty_files"]) == 1
    assert result["audio_content_validated"] is False
