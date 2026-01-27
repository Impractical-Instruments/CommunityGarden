using System.IO;
using UnrealBuildTool;

public class IIVision : ModuleRules
{
    public IIVision(ReadOnlyTargetRules target) : base(target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        bUseRTTI = true;

        PublicDependencyModuleNames.AddRange([
            "Core",
            "CoreUObject",
            "Engine",
            "RenderCore",
            "RHI"
        ]);
    }
}
