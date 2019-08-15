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

import com.jcraft.jsch.JSch;
import com.jcraft.jsch.JSchException;
import com.jcraft.jsch.ProxyHTTP;
import com.jcraft.jsch.Session;
import java.io.Console;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintStream;
import java.util.ArrayList;
import java.util.Scanner;
import java.util.logging.Level;
import java.util.logging.Logger;
import org.apache.commons.lang3.SystemUtils;

/**
 *
 * @author porfanid
 */
public final class User implements UserInterface{

    private final PrintStream out;
    private final PrintStream err;
    private final InputStream in;
    public final boolean isInUoi;
    
    private String username;
    private String password;
    
    public User()
    {
        out=System.out;
        err=System.err;
        in=System.in;
        
        
        Scanner keyboard=new Scanner(in);
        
        refreshCredentials();
        
        if(!((IP.LOCAL.toString().toLowerCase().startsWith("opti7020ws"))&&(IP.REMOTE.toString().toLowerCase().startsWith("hp6000ws"))))
        {
            isInUoi=false;
        }
        else{
            if(!SystemUtils.IS_OS_LINUX){
                isInUoi=false;
            }
            else{
                isInUoi=getLocation(keyboard);
            }
        }
    }
    
    
    
    private String[] getCredentials(Scanner keyboard)
    {
        out.print("Please enter your username:");
            String localUsername=keyboard.nextLine();
            String locaslPassword;
            out.print("Please enter your password:");
            
            
            locaslPassword=keyboard.nextLine();
            
            return new String[]{localUsername,locaslPassword};
    }
    
    public boolean getLocation(Scanner keyboard)
    {
        while(true)
        {
            out.print("Are You using a computer from the pep Lab?:");
            String response=keyboard.nextLine();
            try{
                return Boolean.parseBoolean(response);
                
            }
            catch(Exception e){
                out.println("Wrong response.Please try again.");
            }
        }
    }
    
    
    @Override
    public ArrayList<Assignment> getAssignments() {
        
        ArrayList<Assignment> assignments=new ArrayList<>();
        
       PrintStream out=getOutputStream(); 
       out.println("Please enter your lessons. Type \"Done\" when you are done.");
       Scanner keyboard=new Scanner(this.getInputStream());
       String response;
       while(true)
       {
           response=keyboard.nextLine();
            try {
                Assignment current=new Assignment(new File(response));
                assignments.add(current);
            } catch (FileNotFoundException ex) {
                if(response.toLowerCase().trim().equals("done"))
                {
                    return assignments;
                }
                else
                {
                    out.println("Wrong response. Please try again.");
                }
            }
       }
    }

    @Override
    public String getLesson() {
        return "test@cse74134";
    }
    
    
    
    public IP getServer() {
        return TurnIn.SERVER;
    }
    
    
    
    @Override
    public String toString()
    {
        return username.substring(4);
    }

    @Override
    public PrintStream getOutputStream() {
        return out;
    }

    @Override
    public PrintStream getErrorStream() {
        return err;
    }

    @Override
    public InputStream getInputStream() {
        return in;
    }

    @Override
    public void close() throws IOException {
        in.close();
        out.close();
        err.close();
    }

    @Override
    public boolean isInUoi() {
        return isInUoi;
    }

    

    @Override
    public String[] creds() {
        return new String[]{this.username,this.password};
    }

    @Override
    public void refreshCredentials() {
        Scanner keyboard=new Scanner(in);
        String[] creds=getCredentials(keyboard);
        username=creds[0];
        password=creds[1];
    }
}