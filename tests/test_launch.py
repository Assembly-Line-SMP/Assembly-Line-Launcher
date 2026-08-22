from pathlib import Path

from launcher.auth.models import Account, AccountType
from launcher.core.instance import Instance, InstanceMetadata
from launcher.core.launch import LaunchSettings, build_launch_command
from launcher.core.loader_installer import LoaderProfile
from launcher.core.vanilla_installer import VanillaVersionInfo


def test_launch_uses_minecraft_version_for_version_name(tmp_path):
    metadata = InstanceMetadata(
        id="test",
        name="Test",
        modrinth_version_id="pack-id",
        modrinth_version_number="2.3.1",
        minecraft_version="1.21.1",
        loader_id="neoforge",
        loader_version="21.1.248",
        java_major=21,
    )
    instance = Instance(tmp_path, metadata)
    vanilla = VanillaVersionInfo(
        version_id="1.21.1",
        client_jar=Path("client.jar"),
        main_class="net.minecraft.client.main.Main",
        libraries=[],
        natives_dir=tmp_path / "natives",
        asset_index_id="17",
        assets_dir=tmp_path / "assets",
        minecraft_arguments=None,
        game_arguments=["--version", "${version_name}"],
    )
    loader = LoaderProfile(
        main_class="cpw.mods.bootstraplauncher.BootstrapLauncher",
        extra_classpath=[],
        extra_game_arguments=[],
        extra_jvm_arguments=[],
        profile_id="neoforge-21.1.248",
    )
    account = Account(
        id="account",
        username="player",
        uuid="00000000-0000-0000-0000-000000000000",
        type=AccountType.CRACKED,
    )

    command = build_launch_command(
        Path("java"), instance, vanilla, loader, account, LaunchSettings()
    )

    assert command[command.index("--version") + 1] == "neoforge-21.1.248"