/* 
 * The MIT License
 *
 * Copyright 2019 porfanid.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */
package turnin;

import com.jcraft.jsch.ChannelSftp;
import com.jcraft.jsch.SftpException;
import java.io.File;
import java.io.FileNotFoundException;
import java.nio.file.Path;

/**
 *
 * @author porfanid
 */
public class Assignment {
    
    public Path PATH;
    public boolean hasBeenUploaded;
    
    public Assignment(File file) throws FileNotFoundException
    {
        hasBeenUploaded=false;
        if(!file.exists())
        {
            throw new FileNotFoundException();
        }
        PATH=file.toPath();
    }
    
    public String toString()
    {
        return PATH.toString();
    }
    
    private boolean makeDir(ChannelSftp sftpChannel,String dest)
    {
        try {
            
            sftpChannel.mkdir(dest);
            return true;
        } catch (SftpException ex) {
            return false;
        }
    }
    
    public String getPath(String delimitor)
    {
        String[] temp=PATH.toString().split("\\\\");
        String output="";
        for(String i:temp)
        {
            output+=i+delimitor;
        }
        try{
            output=output.substring(0,output.length()-1);
        }catch(StringIndexOutOfBoundsException e)
        {
            
        }
        return output;
    }
    
    public boolean uploadFile(ChannelSftp sftpChannel,String folder)
    {
        try {
            String from=PATH.toString();
            
            
            
            String to=folder+"/"+PATH.toFile().getName();
            
            //System.out.println(to);
            File temp=new File(to);
            PATH=temp.toPath();
            
            //System.out.println("New Path: "+PATH);
            makeDir(sftpChannel,folder);
            
            //System.out.println("\t"+from+"\n\t"+to);
            
            sftpChannel.put(from, to);
            return true;
        } catch (SftpException ex) {
            return false;
        }
    }
}