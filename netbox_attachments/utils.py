from pathlib import Path

def attachment_upload(instance, filename: str) -> str:
    """
    Return a path for uploading file attachments.
    """
    base_path = Path("netbox-attachments")
    # instance path example: netbox-attachments/virtual_machine/42
    instance_path = base_path / instance.content_type.name / str(instance.object_id)
    filename_suffix = Path(filename).suffix

    # rename the file to the provided name, if any. attempt to preserve the file extension.
    if instance.name and Path(instance.name).suffix == filename_suffix:
        # provided name already has same extension
        filepath = instance_path / instance.name
    elif instance.name:
        # no extension in name. adding it
        filepath = instance_path / (instance.name + filename_suffix)
    else:
        # no name provided. using default filename
        filepath = instance_path / filename

    return str(filepath)
