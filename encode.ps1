$sourceRoot = "C:/traverse/Cool-Chic/data/source" # Needs full path
$resolution = "1k"

$typeToFilename = @{
    "diff"      = "diff"
    "normal_xy" = "nor_gl_xy"
    "rough"     = "rough"
    "rm"        = "rm"
}

$datasets = @(
    @{ texture_name = "Rails001";        texture_types = "diff,normal_xy,rm"    }
    @{ texture_name = "Bricks090";       texture_types = "diff,normal_xy,rough" }
    @{ texture_name = "Carpet015";       texture_types = "diff,normal_xy,rough" }
    @{ texture_name = "MetalPlates013";  texture_types = "diff,normal_xy,rm"    }
    @{ texture_name = "PavingStones070"; texture_types = "diff,normal_xy,rough" }
    @{ texture_name = "Wood063";         texture_types = "diff,normal_xy,rough" }
    @{ texture_name = "aerial_rocks_02"; texture_types = "diff,normal_xy,rough" }
    @{ texture_name = "forrest_sand_01"; texture_types = "diff,normal_xy,rough" }
    @{ texture_name = "red_dirt_mud_01"; texture_types = "diff,normal_xy,rough" }
    @{ texture_name = "roof_09";         texture_types = "diff,normal_xy,rough" }
)

foreach ($dataset in $datasets) {
    $textureName = $dataset.texture_name
    $textureDir  = "$sourceRoot/$textureName/$resolution"

    foreach ($type in ($dataset.texture_types -split ",")) {
        $filename = $typeToFilename[$type]
        if (-not $filename) {
            Write-Warning "Unknown texture type '$type' for $textureName -- skipping."
            continue
        }

        $inputPath  = "$textureDir/$filename.png"
        $outputPath = "$textureDir/$filename.cool"
        $workdir    = "./workdir/$textureName/$filename"

        if (-not (Test-Path $inputPath)) {
            Write-Warning "Input not found, skipping: $inputPath"
            continue
        }

        New-Item -ItemType Directory -Force -Path $workdir | Out-Null

        Write-Host "Encoding $textureName / $filename ..."

        $encodeArgs = @(
            "cc_encode.py",
            "-i=$inputPath",
            "-o=$outputPath",
            "--workdir=$workdir",
            "--dec_cfg_residue=cfg/dec/intra/hop7.cfg",
            "--n_itr=10000",
            "--lmbda=0.001"
        )
        python @encodeArgs

        if ($LASTEXITCODE -ne 0) {
            Write-Error "Encoding failed for $textureName / $filename"
            exit $LASTEXITCODE
        }
    }
}

Write-Host "All textures encoded successfully."