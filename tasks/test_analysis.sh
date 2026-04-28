#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)
WORKSPACE_ROOT=$(cd -- "${REPO_ROOT}/.." && pwd)
PYTHON_SCRIPT="${REPO_ROOT}/tasks/test_analysis.py"
DATA_ROOT="${DATA_ROOT:-${WORKSPACE_ROOT}/Data}"
RESULTS_ROOT="${REPO_ROOT}/results/NLPanalysis"
ENV_NAME="voicedeepfake"
JOBS="${JOBS:-24}"
ACTIVE_BATCH_PID=""
ACTIVE_BATCH_PGID=""

mkdir -p "${RESULTS_ROOT}"

if ! command -v conda >/dev/null 2>&1; then
	echo "conda not found in PATH" >&2
	exit 1
fi

if ! command -v setsid >/dev/null 2>&1; then
	echo "setsid not found in PATH" >&2
	exit 1
fi

if [[ ! -f "${PYTHON_SCRIPT}" ]]; then
	echo "Analysis script not found: ${PYTHON_SCRIPT}" >&2
	exit 1
fi

if [[ ! -d "${DATA_ROOT}" ]]; then
	echo "Data root not found: ${DATA_ROOT}" >&2
	exit 1
fi

stop_active_batch() {
	local signal="${1:-TERM}"

	if [[ -n "${ACTIVE_BATCH_PGID}" ]]; then
		echo "[$(date '+%F %T')] Forwarding ${signal} to batch process group ${ACTIVE_BATCH_PGID}" >&2
		kill -"${signal}" -- "-${ACTIVE_BATCH_PGID}" 2>/dev/null || true
	elif [[ -n "${ACTIVE_BATCH_PID}" ]]; then
		echo "[$(date '+%F %T')] Forwarding ${signal} to batch pid ${ACTIVE_BATCH_PID}" >&2
		kill -"${signal}" "${ACTIVE_BATCH_PID}" 2>/dev/null || true
	fi
}

handle_interrupt() {
	echo "[$(date '+%F %T')] Interrupt received, stopping active batch..." >&2
	stop_active_batch TERM
	if [[ -n "${ACTIVE_BATCH_PID}" ]]; then
		wait "${ACTIVE_BATCH_PID}" 2>/dev/null || true
	fi
	exit 130
}

trap handle_interrupt INT TERM

run_batch() {
	local dataset_name="$1"
	local input_dir="$2"
	local prefix="$3"
	local extension_filter="${4:-}"
	local dataset_results_dir="${RESULTS_ROOT}/${prefix}"
	local log_dir="${dataset_results_dir}/batch_logs"
	local log_file="${log_dir}/${prefix}_$(date +%Y%m%d-%H%M%S).log"
	local batch_status

	if [[ ! -d "${input_dir}" ]]; then
		echo "Input directory not found for ${dataset_name}: ${input_dir}" >&2
		exit 1
	fi

	mkdir -p "${log_dir}"

	echo "[$(date '+%F %T')] Starting ${dataset_name}"
	echo "[$(date '+%F %T')] Results directory: ${dataset_results_dir}"
	echo "[$(date '+%F %T')] Log file: ${log_file}"
	echo "[$(date '+%F %T')] Jobs: ${JOBS}"

	setsid bash -c '
		set -euo pipefail
		cmd=(
			conda run --no-capture-output -n "$1"
			python -u "$2"
			"$3"
			--prefix "$4"
			--jobs "$5"
			--results-dir "$6"
			--skip-existing
		)
		if [[ -n "$7" ]]; then
			cmd+=(--extensions "$7")
		fi
		"${cmd[@]}" 2>&1 | tee "$8"
	' _ "${ENV_NAME}" "${PYTHON_SCRIPT}" "${input_dir}" "${prefix}" "${JOBS}" "${dataset_results_dir}" "${extension_filter}" "${log_file}" &

	ACTIVE_BATCH_PID=$!
	ACTIVE_BATCH_PGID=$(ps -o pgid= "${ACTIVE_BATCH_PID}" | tr -d ' ')
	echo "[$(date '+%F %T')] Active batch pid=${ACTIVE_BATCH_PID} pgid=${ACTIVE_BATCH_PGID}"

	set +e
	wait "${ACTIVE_BATCH_PID}"
	batch_status=$?
	set -e

	ACTIVE_BATCH_PID=""
	ACTIVE_BATCH_PGID=""

	if [[ ${batch_status} -ne 0 ]]; then
		return "${batch_status}"
	fi

	echo "[$(date '+%F %T')] Finished ${dataset_name}"
}

# run_batch "LibriSpeech test-clean" "${DATA_ROOT}/LibriSpeech/test-clean" "LibriSpeech_test_clean" ".flac"
# run_batch "LibriSpeech train-clean-100" "${DATA_ROOT}/LibriSpeech/train-clean-100" "LibriSpeech_train_clean_100" ".flac"

run_batch "TTS IMS-Toucan" "${DATA_ROOT}/TTS/IMS-Toucan" "TTS_IMS-Toucan" ".wav"
