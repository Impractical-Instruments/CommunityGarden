using System.IO;
using UnrealBuildTool;

public class OrbbecSensor : ModuleRules
{
    public OrbbecSensor(ReadOnlyTargetRules target) : base(target)
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

        PrivateDependencyModuleNames.AddRange([
            "Projects"
        ]);

        var pluginRoot = Path.GetFullPath(Path.Combine(ModuleDirectory, "..", ".."));
        var thirdParty = Path.Combine(pluginRoot, "ThirdParty", "OrbbecSDK");

        PublicIncludePaths.Add(Path.Combine(thirdParty, "Include"));

        if (target.Platform != UnrealTargetPlatform.Win64)
        {
            return;
        }
        
        
        
        var libDir = Path.Combine(thirdParty, "Lib");
        PublicAdditionalLibraries.Add(Path.Combine(libDir, "OrbbecSDK.lib"));

        var binDir = Path.Combine(thirdParty, "Bin");
        StageDll(binDir, "OrbbecSDK.dll");
    }

    private void StageDll(string binDir, string dllName)
    {
        var fullPath = Path.Combine(binDir, dllName);

        // Delay-load at runtime (avoids hard load at startup)
        PublicDelayLoadDLLs.Add(dllName);

        // Ensure packaged output includes the DLL next to the exe
        RuntimeDependencies.Add("$(TargetOutputDir)/" + dllName, fullPath);
        RuntimeDependencies.Add(fullPath);
    }
}
