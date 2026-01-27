using UnrealBuildTool;

public class FlowerBedsEditorTarget : TargetRules
{
	public FlowerBedsEditorTarget( TargetInfo target) : base(target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.V6;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_7;
		ExtraModuleNames.Add("FlowerBeds");
	}
}
