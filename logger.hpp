/*
 * Function: General log header file for cpp 
 * Usage: include this file, LOG(INFO) << "Debug message.";
 */
#ifndef _LOGGER_HPP_
#define _LOGGER_HPP_

#include <iostream>
#include <sstream>
#include <iomanip>
#include <ctime>

enum LogLevel { DEBUG, INFO, WARNING, ERROR, FATAL };

// ANSI color code
const std::string COLOR_RESET = "\033[0m";
const std::string COLOR_DEBUG = "\033[37m";   // white text
const std::string COLOR_INFO = "\033[34m";    // blue text
const std::string COLOR_WARNING = "\033[33m"; // yellow text
const std::string COLOR_ERROR = "\033[31m";   // red text
const std::string COLOR_FATAL = "\033[41;37m"; // red background, white text

// get current time 
inline std::string getCurrentTime() {
    std::time_t now = std::time(nullptr);
    std::tm* tm_info = std::localtime(&now);
    std::ostringstream oss;
    oss << std::put_time(tm_info, "%Y-%m-%d %H:%M:%S");
    return oss.str();
}

// log stream class
class LogStream {
public:
    LogStream(LogLevel level, const char* file, int line)
        : _level(level), _file(file), _line(line) {
        _stream << getCurrentTime() << " " << file << ":" << line << " ";
        _stream << logLevelToString(level) << "\t";
        // set color
        _stream << logLevelColor(level);
    }

    ~LogStream() {
        // reset color and output log
        _stream << COLOR_RESET << std::endl;
        std::cerr << _stream.str(); // Output to the standard error stream (can be changed to a file)
    }

    std::ostream& stream() {
        return _stream;
    }

private:
    std::string logLevelToString(LogLevel level) {
        switch (level) {
            case DEBUG: return "DEBUG";
            case INFO: return "INFO";
            case WARNING: return "WARNING";
            case ERROR: return "ERROR";
            case FATAL: return "FATAL";
            default: return "UNKNOWN";
        }
    }

    std::string logLevelColor(LogLevel level) {
        switch (level) {
            case DEBUG: return COLOR_DEBUG;
            case INFO: return COLOR_INFO;
            case WARNING: return COLOR_WARNING;
            case ERROR: return COLOR_ERROR;
            case FATAL: return COLOR_FATAL;
            default: return COLOR_RESET;
        }
    }

    LogLevel _level;
    const char* _file;
    int _line;
    std::ostringstream _stream;
};

#define LOG(level) LogStream(level, __FILE__, __LINE__).stream()

// #define LOG_INFO LOG(INFO)
// #define LOG_DEBUG LOG(DEBUG)
// #define LOG_WARNING LOG(WARNNING)
// #define LOG_ERROR LOG(ERROR)
// #define LOG_FATAL LOG(FATAL)

#endif // end of _LOGGER_HPP_

