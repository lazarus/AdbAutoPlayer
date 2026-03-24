use crate::{LogLevel, LogMessage};
use serde_json::Value;
use std::fs;
use tauri::{AppHandle, Emitter, Manager};

#[tauri::command]
pub fn save_settings(
    app_handle: AppHandle,
    profile_index: u8,
    file_name: String,
    json_data: String,
) -> Result<(), String> {
    // Parse JSON string into a serde_json::Value
    let parsed_json: Value =
        serde_json::from_str(&json_data).map_err(|e| format!("Invalid JSON: {e}"))?;

    // Convert serde_json::Value into a serde-compatible structure for TOML
    let toml_value = toml::Value::try_from(parsed_json)
        .map_err(|e| format!("Failed to convert JSON to TOML: {e}"))?;

    // Serialize to pretty TOML string
    let toml_string = toml::to_string_pretty(&toml_value)
        .map_err(|e| format!("Failed to serialize TOML: {e}"))?;

    let config_dir = app_handle
        .path()
        .app_config_dir()
        .expect("Failed to get config directory");

    let profile_path = config_dir.join(profile_index.to_string());

    let settings_path = profile_path.join(&file_name);

    fs::create_dir_all(&profile_path)
        .map_err(|e| format!("Failed to create config directories: {e}"))?;

    // Write TOML string to file
    fs::write(&settings_path, toml_string).map_err(|e| format!("Failed to write file: {e}"))?;

    let path_display = settings_path.display().to_string();
    let message = format!("Settings saved: {path_display}");

    app_handle
        .emit(
            "log-message",
            LogMessage::new(LogLevel::INFO, message).with_profile_index(profile_index),
        )
        .expect("Failed to emit log-message");

    Ok(())
}
