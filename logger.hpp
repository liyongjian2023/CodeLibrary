/***********************************************************
 * Function: General log header file for cpp 
 * Usage: include this file, LOG(DEBUG) << "Debug message.";
 ***********************************************************/

#ifndef _LOGGER_HPP_
#define _LOGGER_HPP_

#include <iostream>
#include <sstream>
#include <iomanip>
#include <ctime>
#include <string>

// Enum for log levels
enum LogLevel
{
    DEBUG,
    INFO,
    WARN,
    ERROR,
    FATAL
};

// ANSI color codes
const std::string COLOR_RESET = "\033[0m";
const std::string COLOR_DEBUG = "\033[37m";    // white text
const std::string COLOR_INFO = "\033[34m";     // blue text
const std::string COLOR_WARN = "\033[33m";  // yellow text
const std::string COLOR_ERROR = "\033[31m";    // red text
const std::string COLOR_FATAL = "\033[41;37m"; // red background, white text

// Get the current time
inline std::string getCurrentTime()
{
    std::time_t now = std::time(nullptr);
    std::tm *tm_info = std::localtime(&now);
    std::ostringstream oss;
    oss << std::put_time(tm_info, "%Y-%m-%d %H:%M:%S");
    return oss.str();
}

// Extract file name from file path
inline std::string extractFileName(const std::string &filePath)
{
    size_t pos = filePath.find_last_of("/\\");
    if (pos == std::string::npos)
        return filePath;
    return filePath.substr(pos + 1);
}

// Log stream class
class LogStream
{
public:
    LogStream(LogLevel level, const char *file, const char *func, int line)
        : _level(level), _file(file), _func(func), _line(line)
    {
        _stream << getCurrentTime() << " ";
        _stream << extractFileName(file) << ":" << func << "():" << line << " ";
        _stream << logLevelToString(level) << " | ";
        _stream << logLevelColor(level);
    }

    ~LogStream()
    {
        _stream << COLOR_RESET << std::endl;
        std::cerr << _stream.str(); // Output to the standard error stream (can be changed to a file)
    }

    std::ostream &stream()
    {
        return _stream;
    }

private:
    std::string logLevelToString(LogLevel level)
    {
        switch (level)
        {
        case DEBUG:
            return "DEBUG";
        case INFO:
            return "INFO";
        case WARN:
            return "WARN";
        case ERROR:
            return "ERROR";
        case FATAL:
            return "FATAL";
        default:
            return "UNKNOWN";
        }
    }

    std::string logLevelColor(LogLevel level)
    {
        switch (level)
        {
        case DEBUG:
            return COLOR_DEBUG;
        case INFO:
            return COLOR_INFO;
        case WARN:
            return COLOR_WARN;
        case ERROR:
            return COLOR_ERROR;
        case FATAL:
            return COLOR_FATAL;
        default:
            return COLOR_RESET;
        }
    }

    LogLevel _level;
    const char *_file;
    const char *_func;
    int _line;
    std::ostringstream _stream;
};

#define LOG(level) LogStream(level, __FILE__, __func__, __LINE__).stream()

// #define LOG_INFO LOG(INFO)
// #define LOG_DEBUG LOG(DEBUG)
// #define LOG_WARN LOG(WARNNING)
// #define LOG_ERROR LOG(ERROR)
// #define LOG_FATAL LOG(FATAL)

#endif // end of _LOGGER_HPP_

